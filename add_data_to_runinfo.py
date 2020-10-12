import argparse
import uuid

from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import Consumer, Producer
from streaming_data_types import deserialise_pl72, serialise_pl72

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
        "children": [],
        "attributes": [{"name": "NX_class", "values": nx_class}],
    }


def _create_dataset(name, values):
    return {"type": "dataset", "name": name, "attributes": [], "values": values}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amend data to runinfo messages")
    parser.add_argument("-b", "--broker")
    args = parser.parse_args()

    broker = args.broker
    conf = {"bootstrap.servers": broker, "group.id": str(uuid.uuid4())}
    admin_client = AdminClient(conf)
    cons = Consumer(conf)
    prod = Producer(conf)
    topics = [topic + "_runInfo" for topic in INST_NAMES]
    print(f"subscribing to {topics}")
    cons.subscribe(topics=topics)
    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = cons.poll(1.0)
            if msg is None:
                continue
            message_topic = msg.topic()
            instrument_name = message_topic.split("_runInfo")[0]
            des = deserialise_pl72(msg.value())

            structure = des.nexus_structure
            entry = _create_group("raw_data_1", "NXentry")
            detector_1 = _create_group("detector_1", "NXdetector")
            detector_1["children"].append(structure["entry"]["events"])
            entry["children"].append(detector_1)
            entry["children"].append(_create_dataset("beamline", instrument_name))
            entry["raw_data_1"].append(
                _create_dataset("name", instrument_name)
            )  # these seem to be the same

            new_run_message = serialise_pl72(
                filename=des.filename,
                start_time=des.start_time,
                stop_time=des.stop_time,
                run_name=des.run_name,
                service_id=des.service_id,
                instrument_name=des.instrument_name,
                broker=des.broker,
                nexus_structure=str(entry),
                job_id=des.job_id
            )
            prod.produce(topic="ALL_runInfo", value=new_run_message)
            print(f"produced: {entry}")
        except KeyboardInterrupt:
            break

    cons.close()
