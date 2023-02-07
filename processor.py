
def normalizeIssue(eventData, issueData):
    payload = {
        "exception" : {}
    }

    if eventData is not None and len(eventData["entries"]) > 0:
        dataValues = eventData["entries"][0]["data"]["values"][0] or None
        if len(eventData["entries"]) > 1:
            breadcrumbs = eventData["entries"][1]["data"]
            payload["breadcrumbs"] = breadcrumbs
            
        if dataValues is not None:
            error = {
                "type" : dataValues["type"],
                "value" : dataValues["value"],
                "stacktrace" : normalizeStackTrace(dataValues["stacktrace"]),
                "mechanism" : dataValues["mechanism"]
            }
            payload["exception"]["values"] = [error]
            payload["level"] = issueData["level"]
            payload["platform"] = eventData["platform"]
            payload["timestamp"] = eventData["dateCreated"]
            payload["sdk"] = eventData["sdk"]
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

def normalizeStackTrace(stacktrace):
    payload = {
        "frames" : []
    }

    if "frames" in stacktrace:
        for frame in stacktrace["frames"]:
            obj = {}
            obj["filename"] = frame["absPath"] or frame["filename"]
            obj["function"] = frame["function"]
            obj["in_app"] = frame["inApp"] or frame["in_app"]
            obj["lineno"] = frame["lineNo"]
            obj["colno"] = frame["colNo"]
            payload["frames"].append(obj)
    
    return payload





