import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from render_api import get_active_key, deploy_service
from config import API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class DeployState(StatesGroup):
    asking_repo = State()
    asking_vars = State()

@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Create Web Service", callback_data="deploy_new"))
    builder.row(types.InlineKeyboardButton(text="ℹ️ Help / Support", callback_data="help"))
    
    await message.answer("👋 **Render Multi-ID Deployer**\n\nNiche diye gaye button se deployment shuru karein.", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "deploy_new")
async def ask_repo_link(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("🔗 Apne **GitHub Repository** ka link bhejiye:\n(Example: `https://github.com/user/bot-repo`)")
    await state.set_state(DeployState.asking_repo)
    await call.answer()

@dp.message(DeployState.asking_repo)
async def get_repo_and_ask_vars(message: types.Message, state: FSMContext):
    if "github.com" not in message.text:
        await message.answer("❌ Invalid GitHub Link! Dubara bhejiye.")
        return
    
    await state.update_data(repo=message.text)
    await message.answer("📋 Ab apne **Variables** bhejiye.\nFormat:\n`TOKEN=123\nID=456`...")
    await state.set_state(DeployState.asking_vars)

@dp.message(DeployState.asking_vars)
async def process_deployment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    repo = data['repo']
    
    # Parse variables
    env_vars = {}
    for line in message.text.split('\n'):
        if '=' in line:
            k, v = line.split('=', 1)
            env_vars[k.strip()] = v.strip()

    status_msg = await message.answer("🔍 Searching for available slot in Render IDs...")
    
    key = await get_active_key()
    if not key:
        await status_msg.edit_text("❌ Sabhi Render IDs (10/10) full ho chuki hain!")
        await state.clear()
        return

    await status_msg.edit_text("🚀 Deploying your service on Render... Please wait.")
    
    res, status = await deploy_service(key, repo, f"User-{message.from_user.id}", env_vars)

    if status == 201:
        await status_msg.edit_text(f"✅ **Deployment Successful!**\n\n**Service ID:** `{res['id']}`\n**Status:** Building...")
    else:
        await status_msg.edit_text(f"❌ **Error:** {res.get('message', 'Something went wrong')}")
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
