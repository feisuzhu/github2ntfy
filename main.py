# -*- coding: utf-8 -*-

# -- stdlib --
import hmac
import json
from ssl import ALERT_DESCRIPTION_ACCESS_DENIED
import requests
import os

# -- third party --
from fastapi import FastAPI, Header, Request

# -- own --

# -- code --
NTFY_ENDPOINT = os.environ['NTFY_ENDPOINT']
NTFY_TOPIC = os.environ.get('NTFY_TOPIC', 'GitHub')
GIT_WEBHOOK_SECRET = os.environ['GIT_WEBHOOK_SECRET'].encode()

app = FastAPI()

def calc_sig(data, secret):
    return hmac.new(secret, data, 'sha256').hexdigest()


def transform(name, ev):
    common = {
        'topic': NTFY_TOPIC,
    }

    if name == 'issue_comment':
        return {
            **common,
            "title": f"@{ev['comment']['user']['login']} 在 Issue #{ev['issue']['number']} 中评论了",
            "message": ev['comment']['body'],
            "actions": [{
                "action": "view",
                "label": "打开",
                "url": ev['comment']['html_url'],
                "clear": True
            }]
        }

    elif name == "pull_request_review_comment":
        return {
            **common,
            "title": f"@{ev['comment']['user']['login']} 在 PR #{ev['pull_request']['number']} 中评论了",
            "message": ev['comment']['body'],
            "actions": [{
                "action": "view",
                "label": "打开",
                "url": ev['comment']['html_url'],
                "clear": True
            }]
        }

    elif name == "pull_request_review":
        action_map = {
            "submitted": "提交了",
            "edited": "编辑了",
            "dismissed": "撤销了",
        }

        return {
            **common,
            "title": f"@{ev['review']['user']['login']} {action_map.get(ev['action'], ev['action'])} PR #{ev['pull_request']['number']} 的 Review",
            "message": ev['review']['body'],
            "actions": [{
                "action": "view",
                "label": "打开",
                "url": ev['review']['html_url'],
                "clear": True
            }]
        }

    elif name == "issues":
        action_map = {
            "opened": "创建了",
            "closed": "关闭了",
            "reopened": "重新打开了",
        }

        return {
            **common,
            "title": f"@{ev['sender']['login']} {action_map.get(ev['action'], ev['action'])} Issue #{ev['issue']['number']}",
            "message": ev['issue']['title'],
            "actions": [{
                "action": "view",
                "label": "打开",
                "url": ev['issue']['html_url'],
                "clear": True
            }]
        }

    elif name == "pull_request":
        action_map = {
            "opened": "打开了",
            "closed": "关闭了",
            "reopened": "重新打开了",
            "synchronize": "更新了"
        }
        return {
            **common,
            "title": f"@{ev['pull_request']['user']['login']} {action_map.get(ev['action'], ev['action'])} PR #{ev['pull_request']['number']}",
            "message": ev['pull_request']['title'],
            "actions": [{
                "action": "view",
                "label": "打开",
                "url": ev['pull_request']['html_url'],
                "clear": True
            }]
        }

    elif name == "star":
        action_map = {
            "created": "🌟",
            "deleted": "Unstar 了",
        }

        return {
            **common,
            "title": f"@{ev['sender']['login']} {action_map.get(ev['action'], ev['action'])} {ev['repository']['full_name']}",
            "message": ev['repository']['description'],
            "actions": [{
                "action": "view",
                "label": "查看 Star 的人",
                "url": ev['sender']['html_url'],
                "clear": True
            }]
        }

    else:
        return {
            **common,
            "title": f"未知事件: {name}.{ev['action']}",
            "message": "redacted",
        }


@app.post("/github")
async def github_hook(req: Request, x_hub_signature: str = Header(...), x_github_event: str = Header(...)):
    body = await req.body()
    sig = calc_sig(body, GIT_WEBHOOK_SECRET)
    if sig == x_hub_signature:
        return {"error": "Signature is not valid"}, 403

    requests.post(NTFY_ENDPOINT, json=transform(x_github_event, json.loads(body)))
    return {}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1666)
