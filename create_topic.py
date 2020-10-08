from confluent_kafka.admin import AdminClient
import argparse
import uuid
from confluent_kafka.cimpl import NewTopic

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="create kafka topic. Default partitions is 1"
    )
    parser.add_argument("-t", "--topic", help="the topic to create")
    parser.add_argument("-b", "--broker", help="the broker to create the topics on")
    parser.add_argument("-p", "--partitions", type=int, default=1)
    args = parser.parse_args()

    broker = args.broker
    conf = {"bootstrap.servers": broker}
    admin_client = AdminClient(conf)

    conf["group.id"] = str(uuid.uuid4())
    topic = args.topic
    partitions = args.partitions
    new_topic = NewTopic(topic, num_partitions=partitions)
    admin_client.create_topics([new_topic])
    admin_client.poll(10)
