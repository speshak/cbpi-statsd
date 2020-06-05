from modules import cbpi
from statsd import StatsClient


DEBUG = False
statsd_client = None

sensor_types = {
        "Flowmeter": "flow",
        "OneWireAdvanced": "temp",
        "OneWire": "temp",
}


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


def send_sensor_data():
    with statsd_client.pipeline() as pipe:
        cbpi.app.logger.info("Logging sensor data to statsd")
        for key, value in cbpi.cache.get("sensors").iteritems():
            if value.hide == 1:
                continue

            sensor_value = value.instance.get_value()

            name = '%s.%d' % (value.type, value.instance.id)
            pipe.gauge(name, sensor_value['value'])


def ferm_sensor_data(pipe, prefix, sensor_id):
    if sensor_id == '':
        return

    sensor = cbpi.cache.get("sensors")[int(sensor_id)]
    pipe.gauge(prefix + sensor_types[sensor.type], sensor.instance.get_value()['value'])


def send_fermenter_data():
    with statsd_client.pipeline() as pipe:
        cbpi.app.logger.info("Logging fermenter data to statsd")

        for key, value in cbpi.cache.get("fermenter").iteritems():
            name = 'fermenter.%d.' % (value.id)
            pipe.gauge(name + "target_temp", value.target_temp)

            ferm_sensor_data(pipe, name, value.sensor)
            ferm_sensor_data(pipe, name, value.sensor2)
            ferm_sensor_data(pipe, name, value.sensor3)


@cbpi.backgroundtask(key="statsd_task", interval=60)
def statsd_background_task(api):
    cbpi.app.logger.info("StatsD task running")
    if statsd_client is None:
        cbpi.app.logger.info("No StatsD client, not sending data")
        return

    send_sensor_data()
    send_fermenter_data()
