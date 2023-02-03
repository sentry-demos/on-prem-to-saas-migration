
def normalizeIssue(eventData, issueData):
    payload = {
        "exception" : {}
    }

    if eventData is not None and len(eventData["entries"]) > 0:
        dataValues = eventData["entries"][0]["data"]["values"][0] or None
        if dataValues is not None:
            error = {
                "type" : dataValues["type"],
                "value" : dataValues["value"],
                "stacktrace" : dataValues["stacktrace"],
                "mechanism" : dataValues["mechanism"]
            }
            payload["exception"]["values"] = [error]
            payload["level"] = issueData["level"]
            payload["platform"] = eventData["platform"]
            payload["timestamp"] = eventData["dateCreated"]
            environment = None
            release = None

            for attr in eventData["tags"] : 
                if attr["key"] == "environment" :
                    environment = attr["value"]
                if attr["key"] == "release":
                    release = attr["value"]

            payload["environment"] = release
            payload["release"] = environment

    return payload


