from logger import customLogger

LOGGER = None

def normalizeIssue(eventData, issueData):
    LOGGER = customLogger.Logger()
    payload = {
        "exception" : {}
    }

    print(eventData)

    if eventData is not None and len(eventData["entries"]) > 0:
        LOGGER.debug("Called")
        LOGGER.debug("Normalizing event data")
        dataValues = eventData["entries"][0]["data"]["values"][0] or None
        if len(eventData["entries"]) > 1:
            if eventData["entries"][1]["type"] == "breadcrumbs":
                breadcrumbs = eventData["entries"][1]["data"]
                payload["breadcrumbs"] = breadcrumbs
            
        if dataValues is not None:
            try:
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
                payload["release"] = eventData["release"]["version"]
                payload["tags"] = eventData["tags"]
                payload["contexts"] = eventData["contexts"]
                environment = None
                release = None

                for attr in eventData["tags"] : 
                    if attr["key"] == "environment" :
                        environment = attr["value"]
                    if attr["key"] == "release":
                        release = attr["value"]

                payload["environment"] = release
                payload["release"] = environment
            except Exception as e:
                LOGGER.error(f'Could not normalize data - Reason: {str(e)}')
        else:
            LOGGER.error("Event object has no data values")
    else:
        LOGGER.error("Event request did not return any data")

    return payload

def normalizeStackTrace(stacktrace):
    payload = {
        "frames" : []
    }

    if "frames" in stacktrace:
        for frame in stacktrace["frames"]:
            print(frame)
            obj = {}
            obj["filename"] = frame["filename"]
            obj["function"] = frame["function"]
            obj["in_app"] = frame["inApp"] or frame["in_app"]
            obj["lineno"] = frame["lineNo"]
            obj["colno"] = frame["colNo"]
            
            if "context" in frame and frame["context"] is not None:
                obj["context"] = frame["context"]
            else:
                properties = ["pre_context", "post_context", "context_line"]
                if all(prop in frame for prop in properties):
                    # do nothing
                    print(properties)

            # post-processed event from sentry sends context under "context" variable but SDK should send it as ["pre_context", "post_context", "context_line"]

            
            if "module" in frame:
                obj["module"] = frame["module"]
            if "package" in frame:
                obj["package"] = frame["package"]
            if "instructionAddr" in frame:
                obj["instructionAddr"] = frame["instructionAddr"]
            if "symbolAddr" in frame:
                obj["symbolAddr"] = frame["symbolAddr"]
            if "rawFunction" in frame:
                obj["rawFunction"] = frame["rawFunction"]
            if "symbol" in frame:
                obj["symbol"] = frame["symbol"]
            if "vars" in frame:
                obj["vars"] = frame["vars"]
            if "errors" in frame:
                obj["errors"] = frame["errors"]
            if "trust" in frame:
                obj["trust"] = frame["trust"]
            if "pre_context" in frame:
                obj["pre_context"] = frame["pre_context"]
            if "post_context" in frame:
                obj["post_context"] = frame["post_context"]
            if "context_line" in frame:
                obj["context_line"] = frame["context_line"]

            payload["frames"].append(obj)
    
    return payload





