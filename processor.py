from sentry import utils

def normalize_issue(eventData, issueData):
    payload = {
        "exception" : {}
    }

    if eventData is not None and len(eventData["entries"]) > 0:
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
                    "stacktrace" : normalize_stacktrace(dataValues["stacktrace"], eventData["platform"]),
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

                payload["environment"] = environment
                payload["release"] = release
            except Exception as e:
                return {
                    "error" : f'Could not normalize data - Reason: {str(e)} - Skipping...'
                }
        else:
            return {
                "error" : "Event object has no data values - Skipping..."
            }
    else:
        return {
            "error" : "Event request did not return any data - Skipping..."
        }

    return payload

def normalize_stacktrace(stacktrace, platform):
    payload = {
        "frames" : []
    }

    if "frames" in stacktrace:
        for frame in stacktrace["frames"]:
            obj = {}
            obj["filename"] = frame["filename"]
            obj["function"] = frame["function"]
            obj["in_app"] = frame["inApp"] or frame["in_app"]
            obj["lineno"] = frame["lineNo"]
            obj["colno"] = frame["colNo"]

            context_all = get_all_context_attr(frame)
            if context_all is not None:
                obj["pre_context"] = context_all["pre_context"]
                obj["context_line"] = context_all["context_line"]
                obj["post_context"] = context_all["post_context"]
            
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

            payload["frames"].append(obj)
    
    return payload

def get_all_context_attr(frame):
    pre_context = []
    context = None
    post_context = []
    if check_context_attrs(frame):
        context_line = utils.replace_all(frame["vars"]["e"], [" ", "'", '"']).lower()
        for line in frame["context"]:
            formatted_str = utils.replace_all(line[1], [" ", "'", '"']).lower()
            if context_line in formatted_str:
                context = line[1]
            else:
                if context is None:
                    pre_context.append(line[1])
                else:
                    post_context.append(line[1])
        return {
            "pre_context" : pre_context,
            "context_line" : context,
            "post_context" : post_context
        }

    return None

def check_context_attrs(frame):
    return ("context" in frame and frame["context"] is not None) and ("vars" in frame and frame["vars"] is not None)





