import argparse
import uuid

from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import Consumer
from streaming_data_types import deserialise_pl72

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
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Amend data to runinfo messages")
    parser.add_argument("-b", "--broker")
    args = parser.parse_args()

    broker = args.broker
    conf = {"bootstrap.servers": broker, "group.id": str(uuid.uuid4())}
    admin_client = AdminClient(conf)
    cons = Consumer(conf)
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
            new_structure = {"raw_data_1": structure["entry"]}
            new_structure["raw_data_1"]["beamline"] = instrument_name

            print(structure)
        except KeyboardInterrupt:
            break

    cons.close()
