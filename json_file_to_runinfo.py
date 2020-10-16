import argparse
import json
import uuid
from confluent_kafka.cimpl import Producer
from streaming_data_types import serialise_pl72, serialise_6s4t
import os
from time import sleep

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

    while True:
        job_id = str(uuid.uuid4())

        file_name = filename.split(os.sep)[-1]

        data["children"][0]["children"][1]["children"][0]["stream"]["shape"][2][
            "edges"
        ] = [float(i) for i in range(5, 20001)]

        structure = json.dumps(data)

        blob = serialise_pl72(
            nexus_structure=structure,
            broker=args.broker,
            filename=f"{str(uuid.uuid4())}.nxs",
            job_id=job_id,
        )
        prod.produce(topic, value=blob)
        prod.poll(5)

        sleep(600)  # increase this to allow more time for the file to write

        stop_msg = serialise_6s4t(job_id=job_id)
        prod.produce(topic, value=stop_msg)
        prod.poll(5)
