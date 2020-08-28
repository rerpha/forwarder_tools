import json
import socket

"""
Loads from the output of CS:INSTLIST and prints all instrument host names.
"""

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="get hostnames for the output of CS:INSTLIST in order to get all instrument IPs in a suitable format to put in CA_ADDR_LIST"
    )
    parser.add_argument("filename")
    parser.add_argument(
        "--suffix", help="the suffix of the full URL to ping, ie .someprefix.co.uk"
    )
    args = parser.parse_args()

    hosts = []

    with open(args.filename) as file:
        json = json.load(file)
        for item in json:
            hostname = item["hostName"]
            full_hostname = f"{hostname.lower()}{args.suffix}"
            host_ip = socket.gethostbyname(full_hostname)
            hosts.append(host_ip)

    print(str(hosts).strip("[").strip("]").replace("'", ""))
