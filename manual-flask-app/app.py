from flask import Flask, render_template,request,redirect,url_for # For flask implementation
from bson import ObjectId # For ObjectId to work
from pymongo import MongoClient
import os

import requests
from random import randrange

#Resource 
from opentelemetry.sdk.resources import Resource

#trace 
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)

#metric
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.metrics import (
    get_meter_provider,
    set_meter_provider,
)

#logging Instrumentation
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Resource Service.name 정의
resource =Resource(attributes={
	"service.name" : "manual-flask-app"
})

# Trace Exporter
trace_provider = TracerProvider(resource=resource)

# processor = BatchSpanProcessor(ConsoleSpanExporter())
console_exporter = ConsoleSpanExporter()
otlp_exporter = OTLPSpanExporter(insecure="true", endpoint="http://signoz-otel-collector.signoz.svc.cluster.local:4317")
span_processor_otlp = BatchSpanProcessor(
		span_exporter=otlp_exporter, 
		max_export_batch_size=512,
		schedule_delay_millis=5000,
    )
span_processor_console = BatchSpanProcessor(
		span_exporter=console_exporter, 
		max_export_batch_size=512,
		schedule_delay_millis=5000,
    )
trace_provider.add_span_processor(span_processor_otlp)
trace_provider.add_span_processor(span_processor_console)

# Sets the global default tracer provider
trace.set_tracer_provider(trace_provider)

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer("manual.flask.todo-app")


# Metric Exporter
exporter = OTLPMetricExporter(insecure=True, endpoint="http://signoz-otel-collector.signoz.svc.cluster.local:4317")
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader])
set_meter_provider(provider)


app = Flask(__name__)
FlaskInstrumentor().instrument(enable_commenter=True, commenter_options={}, app=app)
title = "TODO sample application with Flask and MongoDB"
heading = "TODO Reminder with Flask and MongoDB"

mongoHost = os.getenv("MONGO_HOST", "mongo-db2.manual-flask-app")
client = MongoClient("mongodb://"+mongoHost+":27018", username="admin", password="dbgudwn1!") #host uri
db = client.mymongodb    #Select the database
todos = db.todo #Select the collection name

meter = get_meter_provider().get_meter("sample-flask-app", "0.1.2")

todo_counter = meter.create_up_down_counter("todo_count")

@tracer.start_as_current_span("redirect_url")
def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')


@app.route("/list")
@tracer.start_as_current_span("lists")
def lists ():
		#Display the all Tasks
		todos_l = todos.find()
		a1="active"
		if randrange(10) % 2:
			response = requests.get('https://run.mocky.io/v3/b851a5c6-ab54-495a-be04-69834ae0d2a7')
			response.close()
		else:
			response = requests.get('https://run.mocky.io/v3/1cb67153-a6ac-4aae-aca6-273ed68b5d9e')
			response.close()

		return render_template('index.html',a1=a1,todos=todos_l,t=title,h=heading), 500


@app.route("/")
@app.route("/uncompleted")
@tracer.start_as_current_span("tasks")
def tasks ():
	#Display the Uncompleted Tasks
	todos_l = todos.find({"done":"no"})
	a2="active"
	return render_template('index.html',a2=a2,todos=todos_l,t=title,h=heading)


@app.route("/completed")
@tracer.start_as_current_span("completed")
def completed ():
	#Display the Completed Tasks
	todos_l = todos.find({"done":"yes"})
	a3="active"
	return render_template('index.html',a3=a3,todos=todos_l,t=title,h=heading)


@app.route("/done")
@tracer.start_as_current_span("done")
def done ():
	#Done-or-not ICON
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	if(task[0]["done"]=="yes"):
		todos.update({"_id":ObjectId(id)}, {"$set": {"done":"no"}})
	else:
		todos.update({"_id":ObjectId(id)}, {"$set": {"done":"yes"}})
	redir=redirect_url()	

	return redirect(redir)


@app.route("/action", methods=['POST'])
@tracer.start_as_current_span("action")
def action ():
	#Adding a Task
	name=request.values.get("name")
	desc=request.values.get("desc")
	date=request.values.get("date")
	pr=request.values.get("pr")
	todos.insert({ "name":name, "desc":desc, "date":date, "pr":pr, "done":"no"})
	todo_counter.add(1)
	return redirect("/")


@app.route("/remove")
@tracer.start_as_current_span("remove")
def remove ():
	#Deleting a Task with various references
	key=request.values.get("_id")
	todos.remove({"_id":ObjectId(key)})
	todo_counter.add(-1)
	return redirect("/")


@app.route("/update")
@tracer.start_as_current_span("update")
def update ():
	id=request.values.get("_id")
	task=todos.find({"_id":ObjectId(id)})
	return render_template('update.html',tasks=task,h=heading,t=title)


@app.route("/action3", methods=['POST'])
@tracer.start_as_current_span("action3")
def action3 ():
	#Updating a Task with various references
	name=request.values.get("name")
	desc=request.values.get("desc")
	date=request.values.get("date")
	pr=request.values.get("pr")
	id=request.values.get("_id")
	todos.update({"_id":ObjectId(id)}, {'$set':{ "name":name, "desc":desc, "date":date, "pr":pr }})
	return redirect("/")


@app.route("/search", methods=['GET'])
@tracer.start_as_current_span("search")
def search():
	#Searching a Task with various references

	key=request.values.get("key")
	refer=request.values.get("refer")
	if(key=="_id"):
		todos_l = todos.find({refer:ObjectId(key)})
	else:
		todos_l = todos.find({refer:key})
	return render_template('searchlist.html',todos=todos_l,t=title,h=heading)


@app.route("/generate-error", methods=['GET'])
@tracer.start_as_current_span("generate_error")
def generate_error ():
	if randrange(10) % 2:
		response = requests.get('https://rufn.fmoceky.io/v3/b851a5c6-ab54-495a-be04-69834ae0d2a7')
		response.close()
	elif randrange(10) % 2:
		listf()
	elif randrange(10) % 2:
		map[x] = "e23"
		for x in range(0, 3):
			map[x] = 3
	else:
		a3 = 100/0

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)