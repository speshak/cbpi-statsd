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
                        "Unable to update config parameter", type="danger",
                        timeout=None)

    if statsd_host != "":
        cbpi.notify("StatsD",
                    "Sending sensor data to StatsD server at " + statsd_host,
                    type="success", timeout=None)

        global statsd_client
        statsd_client = StatsClient(host=statsd_host, prefix="cbpi")


@cbpi.initalizer(order=200)
def init(cbpi):
    cbpi.app.logger.info("StatsD plugin initialize")
    init_statsd_client()


@cbpi.backgroundtask(key="statsd_task", interval=60)
def statsd_background_task(api):
    cbpi.app.logger.info("StatsD task running")
    if statsd_client is None:
        cbpi.app.logger.info("No StatsD client, not sending data")
        return

    with statsd_client.pipeline() as pipe:
        cbpi.app.logger.info("Logging data to statsd")
        for key, value in cbpi.cache.get("sensors").iteritems():
            if value.hide == 1:
                continue

            sensor_value = value.instance.get_value()

            name = '%s.%d' % (value.type, value.instance.id)
            pipe.gauge(name, sensor_value['value'])
