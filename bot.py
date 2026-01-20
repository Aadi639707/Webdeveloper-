import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from render_api import get_active_key, deploy_service
from config import API_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# States define karna (User se data lene ke liye)
class DeploySteps(StatesGroup):
    waiting_for_repo = State()
    waiting_for_vars = State()

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Create Web Service", callback_data="start_deploy"))
    await message.answer("Hello! Render Deployer Bot me aapka swagat hai.\nNaya bot deploy karne ke liye niche button dabayein.", reply_markup=builder.as_markup())

# Deployment shuru karne ka handler
@dp.callback_query(F.data == "start_deploy")
async def ask_repo(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🔗 Apne GitHub Repo ka URL bhejiye:")
    await state.set_state(DeploySteps.waiting_for_repo)
    await callback.answer()

# Repo URL milne ke baad
@dp.message(DeploySteps.waiting_for_repo)
async def ask_vars(message: types.Message, state: FSMContext):
    await state.update_data(repo_url=message.text)
    await message.answer("📝 Ab apne **Variables** bhejiye niche diye gaye format mein:\n\n`API_ID=12345\nAPI_HASH=abcd\nBOT_TOKEN=789:xyz`\n\n(Ek line mein ek variable)")
    await state.set_state(DeploySteps.waiting_for_vars)

# Variables milne ke baad Actual Deploy
@dp.message(DeploySteps.waiting_for_vars)
async def do_deploy(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    repo_url = user_data['repo_url']
    
    # Text ko dictionary me convert karna
    try:
        lines = message.text.split('\n')
        env_dict = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in lines if '=' in line}
    except:
        await message.answer("❌ Format galat hai! Dubara try karein (KEY=VALUE).")
        return

    key = await get_active_key()
    status_msg = await message.answer("⏳ Slot check kiya ja raha hai...")
    
    if not key:
        await status_msg.edit_text("❌ Sabhi IDs full hain (20/20 bots deployed)!")
        await state.clear()
        return

    await status_msg.edit_text("🚀 Deployment bhej di gayi hai... Please wait.")
    
    # Render API call
    res, code = await deploy_service(key, repo_url, f"Bot-{message.from_user.id}", env_dict)

    if code == 201:
        dashboard_url = f"https://dashboard.render.com/web/{res['id']}"
        await status_msg.edit_text(f"✅ **Success!**\n\nBot deploy ho raha hai.\nID: `{res['id']}`\n\nAap yahan check kar sakte hain: [Dashboard]({dashboard_url})", parse_mode="Markdown")
    else:
        await status_msg.edit_text(f"❌ **Failed!**\nError: {res.get('message', 'Unknown Error')}")
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
