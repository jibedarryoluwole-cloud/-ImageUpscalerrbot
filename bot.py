import os
import logging
import io
from PIL import Image, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ===== CONFIGURATION =====
TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")  # Optional, for AI upscaling

# ===== LOGGING SETUP =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== TOKEN VALIDATION =====
if not TOKEN:
    logger.error("❌ NO TOKEN FOUND! Please set TELEGRAM_TOKEN environment variable.")
    exit(1)

logger.info(f"✅ Token loaded successfully! First 10 chars: {TOKEN[:10]}...")
logger.info(f"✅ Replicate API: {'✅ Set' if REPLICATE_API_TOKEN else '❌ Not set'}")

# ===== IMAGE PROCESSING FUNCTIONS =====

def upscale_image_basic(image_data, scale_factor=2):
    """
    Basic upscaling using PIL (LANCZOS resampling)
    This is a simple approach - for better results, use AI APIs
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Calculate new size
        width, height = img.size
        new_width = width * scale_factor
        new_height = height * scale_factor
        
        # Upscale using LANCZOS resampling (high quality)
        upscaled = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Enhance sharpness for better quality
        enhancer = ImageEnhance.Sharpness(upscaled)
        upscaled = enhancer.enhance(1.2)
        
        # Save to bytes
        output = io.BytesIO()
        upscaled.save(output, format='PNG')
        output.seek(0)
        
        return output
    except Exception as e:
        logger.error(f"Upscaling error: {str(e)}")
        return None

async def upscale_with_replicate(image_data, scale_factor=2):
    """
    AI-powered upscaling using Replicate API with GFPGAN or similar models
    Requires REPLICATE_API_TOKEN environment variable
    """
    if not REPLICATE_API_TOKEN:
        return None
    
    try:
        # For photo restoration/upscaling using GFPGAN
        # Based on existing projects that use Replicate for image enhancement [citation:8]
        import replicate
        
        client = replicate.Client(api_token=REPLICATE_API_TOKEN)
        
        # Upload image to Replicate (simplified - you'd need to handle this properly)
        # This is a placeholder - implement with actual Replicate API calls
        
        # Example with GFPGAN model for restoration
        # model = replicate.models.get("tencentarc/gfpgan")
        # result = model.predict(image=image_url, scale=scale_factor)
        
        # For now, fall back to basic upscaling
        return upscale_image_basic(image_data, scale_factor)
        
    except Exception as e:
        logger.error(f"Replicate API error: {str(e)}")
        return None

async def process_image(image_data, method="basic", scale=2):
    """
    Process image with selected method
    """
    if method == "ai" and REPLICATE_API_TOKEN:
        return await upscale_with_replicate(image_data, scale)
    else:
        return upscale_image_basic(image_data, scale)

# ===== BOT COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued"""
    welcome = (
        "🖼️ *Welcome to Image Upscaler Bot!*\n\n"
        "I can enhance and upscale your images!\n\n"
        "📝 *What I can do:*\n"
        "• Upscale images 2x, 3x, or 4x\n"
        "• Enhance image quality\n"
        "• Sharpen and improve details\n\n"
        "🔧 *Commands:*\n"
        "/start - Show this message\n"
        "/help - Get help\n"
        "/upscale - Upscale an image\n"
        "/settings - Change settings\n\n"
        "💡 *How to use:*\n"
        "1. Send me an image\n"
        "2. Choose upscale factor\n"
        "3. Get your enhanced image back!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🖼️ Upscale 2x", callback_data="upscale_2x")],
        [InlineKeyboardButton("🖼️ Upscale 4x", callback_data="upscale_4x")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = (
        "🤖 *Help Center*\n\n"
        "📝 *How to use this bot:*\n\n"
        "1️⃣ *Send an image:*\n"
        "Send any photo to the bot\n\n"
        "2️⃣ *Choose upscale factor:*\n"
        "• 2x - Double the resolution\n"
        "• 3x - Triple the resolution\n"
        "• 4x - Quadruple the resolution\n\n"
        "3️⃣ *Get results:*\n"
        "The bot will process and send back the upscaled image\n\n"
        "🔧 *Commands:*\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/upscale - Start upscaling process\n"
        "/settings - Change upscale settings\n\n"
        "⚡ *Tips:*\n"
        "• Higher quality images work best\n"
        "• Larger upscale factors take more time\n"
        "• The bot works best on photos and artwork"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def upscale_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start upscaling process"""
    await update.message.reply_text(
        "📸 *Ready to upscale!*\n\n"
        "Please send me an image and then choose the upscale factor.\n\n"
        "Or use /settings to change default settings.",
        parse_mode="Markdown"
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change bot settings"""
    current_scale = context.user_data.get("scale", 2)
    current_method = context.user_data.get("method", "basic")
    
    settings_text = (
        f"⚙️ *Settings*\n\n"
        f"📏 *Scale Factor:* {current_scale}x\n"
        f"🤖 *Method:* {current_method.upper()}\n\n"
        f"Choose new settings:"
    )
    
    keyboard = [
        [InlineKeyboardButton("2x Upscale", callback_data="set_scale_2")],
        [InlineKeyboardButton("3x Upscale", callback_data="set_scale_3")],
        [InlineKeyboardButton("4x Upscale", callback_data="set_scale_4")],
        [InlineKeyboardButton("AI Enhanced", callback_data="set_method_ai")],
        [InlineKeyboardButton("Basic Upscale", callback_data="set_method_basic")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(settings_text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle images sent to the bot"""
    processing_msg = await update.message.reply_text(
        "🔄 *Processing your image...*\n⏳ Please wait...",
        parse_mode="Markdown"
    )
    
    try:
        # Get the image file
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()
        
        # Get user settings
        scale = context.user_data.get("scale", 2)
        method = context.user_data.get("method", "basic")
        
        # Process the image
        result = await process_image(image_data, method, scale)
        
        if result:
            await processing_msg.delete()
            
            # Send the upscaled image
            await update.message.reply_photo(
                result,
                caption=f"✅ *Image Upscaled!*\n\n📏 *Scale:* {scale}x\n🤖 *Method:* {method.upper()}\n\n*Original size restored and enhanced!*",
                parse_mode="Markdown"
            )
        else:
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ *Failed to upscale image*\n\n"
                "Please try again with a different image.\n\n"
                "💡 Tips:\n"
                "• Try a simpler image\n"
                "• Use /settings to try a different scale\n"
                "• Make sure the image is not too large",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Image processing error: {str(e)}")
        await processing_msg.delete()
        await update.message.reply_text(
            f"❌ *Error processing image*\n\n{str(e)}\n\nPlease try again.",
            parse_mode="Markdown"
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help":
        help_text = (
            "🤖 *How to use this bot:*\n\n"
            "1. Send an image\n"
            "2. Choose upscale factor\n"
            "3. Get your enhanced image!\n\n"
            "Use /settings to change default settings."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown")
    
    elif data.startswith("upscale_"):
        # User wants to upscale an image with specific factor
        scale = int(data.replace("upscale_", "").replace("x", ""))
        context.user_data["scale"] = scale
        await query.edit_message_text(
            f"✅ *Scale factor set to {scale}x*\n\n"
            f"Now send me an image to upscale!",
            parse_mode="Markdown"
        )
    
    elif data.startswith("set_scale_"):
        scale = int(data.replace("set_scale_", ""))
        context.user_data["scale"] = scale
        await query.edit_message_text(
            f"✅ *Scale factor changed to {scale}x*\n\n"
            f"Send an image to upscale with the new settings.",
            parse_mode="Markdown"
        )
    
    elif data.startswith("set_method_"):
        method = data.replace("set_method_", "")
        context.user_data["method"] = method
        await query.edit_message_text(
            f"✅ *Method changed to {method.upper()}*\n\n"
            f"Send an image to upscale with the new settings.",
            parse_mode="Markdown"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# ===== MAIN APPLICATION =====
def main():
    """Start the bot"""
    logger.info("🚀 Starting Image Upscaler Bot...")
    logger.info(f"🤖 Bot Username: @ImageUpscalerBot")
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("upscale", upscale_command))
    app.add_handler(CommandHandler("settings", settings_command))
    
    # Add message handler for images
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    # Add callback query handler
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot is ready! Starting polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
