import argparse
import json
import uuid
from confluent_kafka.cimpl import Producer
from streaming_data_types import serialise_pl72
import os
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add json file nexus structure to runinfo and produce it"
    )
    parser.add_argument("filename")
    parser.add_argument("-b", "--broker")
    args = parser.parse_args()

    conf = {"bootstrap.servers": args.broker}

    prod = Producer(conf)
    topic = "ALL_runInfo"

    filename = args.filename

    with open(args.filename) as json_file:
        data = json.load(json_file)

        file_name = filename.split(os.sep)[-1]

        blob = serialise_pl72(
            nexus_structure=json.dumps(data),
            filename=f"{file_name.split('.json')[0]}.nxs",
            job_id=f"{uuid.uuid4()}",
        )
        prod.produce(topic, value=blob)
        prod.poll(5)
