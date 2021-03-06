import json
import logging
import os

from kafka import KafkaConsumer

import k8scontroller

bootstrap_servers = os.environ.get('KAFKA_SERVERS', 'localhost:9092').split(',')
topic = os.environ.get('KAFKA_TOPIC', 'events')

TEST_TYPE = 'test'
EVENT_TYPE = 'event'
QUERIES_TYPE = 'queries'

UPDATE_ACTION = 'update'
REFRESH_ACTION = 'refresh'
IGNORE_ACTION = 'ignore'


def main():
    consumer = KafkaConsumer(topic, group_id='k8scontroller-eventparser', bootstrap_servers=bootstrap_servers,
                             value_deserializer=lambda m: json.loads(m.decode('utf-8')))

    for message in consumer:
        value = message.value
        type_ = value['type']
        action = value['action']
        if (action == UPDATE_ACTION or action == REFRESH_ACTION) and type_ == EVENT_TYPE:
            data = value['data']
            try:
                if data['tracking'] and data['tokens'].replace(' ', '').replace(',', ''):
                    k8scontroller.apply_eventparser(data['code'], data['tokens'])
                    logging.info('Created event partser for event: %s' % data['code'])
            except KeyError:
                logging.info('Message received was not formatted correctly. Message:\n %s' % data)
        elif (action == UPDATE_ACTION or action == REFRESH_ACTION) and type_ == QUERIES_TYPE:
            tokens = value['data']
            try:
                k8scontroller.update_queries(tokens)
                logging.info('Updated twitter streaming with queries: %s' % tokens)
            except KeyError:
                logging.info('Message received was not formatted correctly. Message:\n %s' % value)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
        level=logging.INFO
    )
    logging.info('Checking Kubernetes connection...')
    logging.info('Kubernetes current pods ips: %s' % k8scontroller.get_pod_ips())

    logging.info('Kafka servers: %s' % ','.join(bootstrap_servers))
    logging.info('Start tracking changes')
    main()
