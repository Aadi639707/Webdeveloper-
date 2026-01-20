import aiohttp
from config import RENDER_KEYS

async def get_active_key():
    async with aiohttp.ClientSession() as session:
        for key in RENDER_KEYS:
            headers = {"Authorization": f"Bearer {key}"}
            async with session.get('https://api.render.com/v1/services?limit=20', headers=headers) as resp:
                if resp.status == 200:
                    services = await resp.json()
                    if len(services) < 10:
                        return key
    return None

async def deploy_service(key, repo_url, service_name, env_dict):
    url = "https://api.render.com/v1/services"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    
    # User ke variables ko Render format mein convert karna
    render_env_vars = [{"key": k, "value": v} for k, v in env_dict.items()]

    data = {
        "type": "web_service",
        "name": service_name,
        "repo": repo_url,
        "autoDeploy": "yes",
        "serviceDetails": {
            "plan": "free",
            "runtime": "python", # Aap ise user se bhi puch sakte hain
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "python bot.py"
        },
        "envVars": render_env_vars
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as resp:
            return await resp.json(), resp.status
          
