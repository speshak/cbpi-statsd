from modules import cbpi
from statsd import StatsClient


DEBUG = False
statsd_client = None


def init_statsd_client():
    statsd_host = cbpi.get_config_parameter("statsd_host", None)

    if statsd_host is None:
        try:
            cbpi.add_config_parameter("statsd_host", "",
                                      "text", "StatsD Hostname")
        except Exception:
            cbpi.notify("StatsD Error",
                        "Unable to update config parameter", type="danger")

    cbpi.app.logger.info(
            "Sending sensor data to StatsD server at " + statsd_host)

    global statsd_client
    statsd_client = StatsClient(host=statsd_host, prefix="cbpi")


@cbpi.initalizer(order=200)
def init(cbpi):
    cbpi.app.logger.info("StatsD plugin initialize")
    init_statsd_client()


@cbpi.backgroundtask(key="statsd_task", interval=60)
def statsd_background_task(api):
    with statsd_client.pipeline() as pipe:
        for key, value in cbpi.cache.get("sensors").iteritems():
            if value.hide == 1:
                continue

            name = '%s.%d' % (value.type, value.instance.id)
            pipe.gauge(name, value.instance.get_value())
