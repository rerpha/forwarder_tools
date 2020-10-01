import json
import argparse

from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import Consumer, NewTopic
import uuid

TOPICS_PER_INST = [
    "_events",
    "_sampleEnv",
    "_runInfo",
    "_monitorHistograms",
    "_detSpecMap",
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="create topics if they dont exist using the output of CS:INSTLIST"
    )
    parser.add_argument("filename")
    parser.add_argument("--broker", help="the broker to create the topics on")
    args = parser.parse_args()

    broker = args.broker
    conf = {"bootstrap.servers": broker}
    admin_client = AdminClient(conf)

    conf["group.id"] = str(uuid.uuid4())
    cons = Consumer(conf)
    topics = cons.list_topics()
    topics_list = topics.topics

    with open(args.filename) as file:
        json = json.load(file)
        for item in json:
            inst_name = item["name"]
            for topic_suffix in TOPICS_PER_INST:
                topic_to_check = inst_name + topic_suffix
                if topic_to_check not in topics_list:
                    print(f"creating {topic_to_check}")
                    new_topic = NewTopic(topic_to_check, num_partitions=1)
                    admin_client.create_topics([new_topic])
    admin_client.poll(10)
