
from confluent_kafka.admin import AdminClient
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="create kafka topic. Default partitions is 1"
    )
    parser.add_argument("-t", "--topic", help="the topic to create")
    parser.add_argument("-b", "--broker", help="the broker to create the topics on")
    args = parser.parse_args()

    broker = args.broker
    conf = {"bootstrap.servers": broker}
    admin_client = AdminClient(conf)
    fs = admin_client.delete_topics([args.topic])
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))

    admin_client.poll(1)
