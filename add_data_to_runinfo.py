import argparse
import json
import uuid

from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import Consumer, Producer
from streaming_data_types import deserialise_pl72, serialise_pl72

CHILDREN = "children"

INST_NAMES = [
    "LARMOR",
    "ALF",
    "DEMO",
    "IMAT",
    "MUONFE",
    "ZOOM",
    "IRIS",
    "IRIS_SETUP",
    "ENGINX_SETUP",
    "HRPD",
    "POLARIS",
    "VESUVIO",
    "ENGINX",
    "MERLIN",
    "RIKENFE",
    "SELAB",
    "EMMA-A",
    "SANDALS",
    "GEM",
    "MAPS",
    "OSIRIS",
    "INES",
    "TOSCA",
    "LOQ",
    "LET",
    "MARI",
    "CRISP",
    "SOFTMAT",
    "SURF",
    "NIMROD",
    "DETMON",
    "EMU",
]


def _create_group(name, nx_class):
    return {
        "type": "group",
        "name": name,
        CHILDREN: [],
        "attributes": [{"name": "NX_class", "values": nx_class}],
    }


def _create_dataset(name, values):
    return {"type": "dataset", "name": name, "attributes": [], "values": values}


def __add_source_info(instrument):
    source = _create_group("source", "NXsource")
    source[CHILDREN].append(_create_dataset("name", "ISIS"))
    source[CHILDREN].append(_create_dataset("probe", "neutrons"))
    source[CHILDREN].append(_create_dataset("type", "Pulsed Neutron Source"))
    instrument[CHILDREN].append(source)


def __get_spectrum_index_edges(monitor_num: int):
    edges = {
        1: (69632.5, 69633.5),
        2: (69633.5, 69634.5),
        3: (69634.5, 69635.5),
        4: (69635.5, 69636.5),
        5: (69636.5, 69637.5),
        6: (69637.5, 69638.5),
        7: (69638.5, 69639.5),
        8: (69639.5, 69640.5),
        9: (69640.5, 69641.5),
    }
    return edges[monitor_num]


def _create_hs00_stream(
    inst_name: str,
    monitor_num: int,
    data_type: str = "uint64",
    edge_type: str = "double",
    error_type: str = "double",
):
    return {
        "type": "stream",
        "stream": {
            "topic": f"{inst_name}_monitorHistograms",
            "source": f"monitor_{monitor_num}",
            "writer_module": "hs00",
            "data_type": data_type,
            "edge_type": edge_type,
            "error_type": error_type,
            "shape": [
                {
                    "size": 1,
                    "label": "period_index",
                    "unit": "ms",
                    "edges": [0.5, 1.5],
                    "dataset_name": "period_index",
                },
                {
                    "size": 1,
                    "label": "spectrum_index",
                    "unit": "ms",
                    "edges": __get_spectrum_index_edges(monitor_num),
                    "dataset_name": "spectrum_index",
                },
                {
                    "size": 19995,
                    "label": "time_of_flight",
                    "unit": "ms",
                    "edges": [float(i) for i in range(5, 20001)],
                    "dataset_name": "time_of_flight",
                },
            ],
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amend data to runinfo messages")
    parser.add_argument("-b", "--broker")
    args = parser.parse_args()
    broker = args.broker
    conf = {"bootstrap.servers": broker, "group.id": str(uuid.uuid4()), 'message.max.bytes': 5000000}
    admin_client = AdminClient(conf)
    cons = Consumer(conf)
    prod = Producer(conf)
    # topics = [topic + "_runInfo" for topic in INST_NAMES]
    topics = ["MERLIN_runInfo"]
    print(f"subscribing to {topics}")
    cons.subscribe(topics=topics)
    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = cons.poll(1.0)
            if msg is None:
                continue
            value = msg.value()
            schema = value[4:8].decode("utf-8")
            if schema != "pl72":  # check schema here
                print(f"received message with schema {schema}, continuing... ")
                continue

            message_topic = msg.topic()
            instrument_name = message_topic.split("_runInfo")[0]
            des = deserialise_pl72(value)

            structure = json.loads(des.nexus_structure)
            entry = _create_group("raw_data_1", "NXentry")

            # Events
            detector_1 = _create_group("detector_1_events", "NXdetector")
            detector_1[CHILDREN] = structure["children"][0]["children"]
            instrument = _create_group("instrument", "NXinstrument")

            __add_source_info(instrument)

            entry[CHILDREN].append(detector_1)
            entry[CHILDREN].append(instrument)
            entry[CHILDREN].append(_create_dataset("beamline", instrument_name))
            entry[CHILDREN].append(
                _create_dataset("name", instrument_name)
            )  # these seem to be the same

            # TODO: sample env
            selog = _create_group("selog", "IXselog")
            entry[CHILDREN].append(selog)

            for i in range(1,10):
                monitor = _create_group(f"monitor_{i}", "NXmonitor")
                monitor[CHILDREN].append(_create_hs00_stream(instrument_name, i))
                entry[CHILDREN].append(monitor)

            new_run_message = serialise_pl72(
                filename=des.filename,
                start_time=des.start_time,
                stop_time=des.stop_time,
                run_name=des.run_name,
                service_id=des.service_id,
                instrument_name=des.instrument_name,
                broker=des.broker,
                nexus_structure=json.dumps(entry),
                job_id=des.job_id,
            )
            prod.produce(topic="ALL_runInfo", value=new_run_message)
            prod.poll(1)
            print(f"produced: {entry}")
        except KeyboardInterrupt:
            break

    cons.close()
