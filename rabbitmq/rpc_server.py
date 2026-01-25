import inspect

import pika
import logging

from rabbitmq.protocol import decode_json, encode_json
from rabbitmq.rabbitmq import Rabbitmq


METHOD_ATTRIBUTE = "method"
ARGS_ATTRIBUTE = "args"


class RPCServer(Rabbitmq):
    """
    Implements some basic operations to make it easier to implement remote procedure call as in
    https://www.rabbitmq.com/tutorials/tutorial-six-python.html
    Subclasses should specialize this and implement the methods that can be invoked from rabbitmq messages.
    For instance, if a message contains a method attribute with "run", then the subclass should implement the "on_run" method.
    Any state should be placed in a database.

    Basically this class sets up the AMQP consumer (method `setup` binds queue/routing key and subscribes). 
    On each message, method `serve` decodes JSON, checks reply_to/correlation_id, validates that the to be called method exists on the server and that required args are present. It builds `reply(msg)` to publish a response and ack the delivery, then calls the resolved method as `method_op(**args, reply_fun=reply)`. Methods must accept a `reply_fun` parameter and invoke it to send the result (as seen in the example method `echo`).
    """
    
    def __init__(self, ip,
                 port,
                 username,
                 password,
                 vhost,
                 exchange,
                 type,
                 ssl = None,
                 ):
        super().__init__(ip=ip,
                         port=port,
                         username=username,
                         password=password,
                         vhost=vhost,
                         exchange=exchange,
                         type=type)
        self._l = logging.getLogger("RPCServer")

    def setup(self, routing_key, queue_name):
        self.connect_to_server()
        self.channel.basic_qos(prefetch_count=1) # type: ignore
        self.channel.queue_declare(queue=queue_name, auto_delete=True) # type: ignore
        self.channel.queue_bind( # type: ignore
            exchange=self.exchange_name,
            queue=queue_name,
            routing_key=routing_key
        )

        # Define the callback that should be called on each message arrival: invoke `serve` on each message.
        self.channel.basic_consume(queue=queue_name, on_message_callback=self.serve) # type: ignore
        self._l.debug(f"Ready to listen for msgs in queue {queue_name} bound to topic {routing_key}")

    def start_serving(self):
        # This will cause the server to start consuming messages (that is, it will wait until a message arrives) and invoking `serve` on each message.
        self.start_consuming()

    def serve(self, ch, method, props, body):
        body_json = decode_json(body)
        self._l.debug(f"Message received: \nf{body_json}")

        # The message shape is expected to be:
        # {
        #   "method": "method_name", # e.g., "echo"
        #   "args": {
        #       "arg1": value1,
        #       "arg2": value2,
        #       ...
        #   }
        # }

        # Check if reply_to is given
        # reply_to is a routing key. It means that the sender expects a reply to be sent to that routing key.
        if props.reply_to is None:
            self._l.warning(f"Message received does not have reply_to. Will be ignored. Message:\n{body_json}.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        routing_key_reply = props.reply_to
        self._l.debug(f"routing_key_reply = f{routing_key_reply}")

        # Correlation id is used to match requests and replies. It's a unique identifier for the request.
        request_id = props.correlation_id
        self._l.debug(f"request_id = f{request_id}")

        # Create short function to reply
        # The idea is that methods invoked can call this function to send the reply without needing to know about the channel, routing key, request id, etc.
        # It allows classes that inherit from RPCServer to focus on implementing the methods that can be invoked remotely without worrying about the underlying messaging details.
        def reply(msg):
            self._l.debug(f"Sending reply msg:\n{msg}")
            ch.basic_publish(exchange='',
                            routing_key=routing_key_reply,
                            properties=pika.BasicProperties(correlation_id=request_id),
                            body=encode_json(msg))
            ch.basic_ack(delivery_tag=method.delivery_tag)

        # Check if method is provided
        if METHOD_ATTRIBUTE not in body_json:
            self._l.warning(f"Message received does not have attribute {METHOD_ATTRIBUTE}. Message:\n{body_json}")
            reply({"error": f"Attribute {METHOD_ATTRIBUTE} must be specified."})
            return

        server_method = body_json[METHOD_ATTRIBUTE]

        # Check if method exists in subclasses
        # Uses reflection to get the method to be invoked from the current instance.
        # Example, if server_method is "echo", it will try to get `self.echo`.
        method_op = getattr(self, server_method, None)
        if method_op is None:
            self._l.warning(f"Method specified does not exist: {server_method}. Message:\n{body_json}")
            reply({"error": f"Method specified does not exist: {server_method}."})
            return

        # Check if args are provided
        if ARGS_ATTRIBUTE not in body_json:
            self._l.warning(
                f"Message received does not have arguments in attribute {ARGS_ATTRIBUTE}. Message:\n{body_json}")
            reply({"error": f"Message received does not have arguments in attribute {ARGS_ATTRIBUTE}."})
            return
        args = body_json[ARGS_ATTRIBUTE]

        # Get method signature and compare it with args provided
        # This ensures that methods are called with the arguments in their signature.
        signature = inspect.signature(method_op)
        if "reply_fun" not in signature.parameters:
            error_msg = f"Method {method_op} must declare a parameter 'reply_fun' that must be invoked to reply to an invokation."
            self._l.warning(error_msg)
            reply({"error": error_msg})
            return
        for arg_name in signature.parameters:
            if arg_name != "reply_fun" and arg_name not in args:
                self._l.warning(
                    f"Message received does not specify argument {arg_name} in attribute {ARGS_ATTRIBUTE}. Message:\n{body_json}")
                reply({"error": f"Message received does not specify argument {arg_name} in attribute {ARGS_ATTRIBUTE}."})
                return

        # Call method with named arguments provided.
        # Example: if method_op is `self.echo` and args is {"msg": "hello"}, it will call
        # `self.echo(msg="hello", reply_fun=reply)`
        method_op(**args, reply_fun=reply)

    def echo(self, msg, reply_fun):
        """
        Example method that is invoked by RPCServer when a message arrives with the method=echo
        """

        """
        This send the reply message back.
        Instead of returning, this solution allows child classes to, e.g., reply and start listening for other messages.
        """
        reply_fun(msg)