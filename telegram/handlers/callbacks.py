import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from telegram.callback_data import VideoCallback, CancelCallback
from agents.orchestrator_agent import OrchestratorAgent
from core.task_manager import task_manager
from telegram.states import ProcessingState

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(VideoCallback.filter())
async def handle_video_confirmation(
    callback_query: types.CallbackQuery,
    callback_data: VideoCallback,
    orchestrator: OrchestratorAgent,
    state: FSMContext
):
    await callback_query.answer()
    message_to_edit = callback_query.message

    if callback_data.action == "start":
        logger.info(f"User {callback_query.from_user.id} confirmed processing for video_id: {callback_data.video_id}")
        
        await state.set_state(ProcessingState.is_processing)
        
        await orchestrator.launch_analysis_task(
            video_id=callback_data.video_id,
            original_message=message_to_edit,
            state=state
        )
        
        cancel_button = types.InlineKeyboardButton(
            text="❌ Отменить обработку",
            callback_data=CancelCallback(
                chat_id=message_to_edit.chat.id,
                message_id=message_to_edit.message_id
            ).pack()
        )
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
        
        await message_to_edit.edit_text(
            "⏳ Обработка началась... Вы можете отменить ее в любой момент.",
            reply_markup=keyboard
        )

    elif callback_data.action == "cancel":
        logger.info(f"User {callback_query.from_user.id} cancelled before starting.")
        await message_to_edit.edit_text("❌ Обработка отменена.", reply_markup=None)

@router.callback_query(CancelCallback.filter())
async def handle_cancel_processing(
    callback_query: types.CallbackQuery,
    callback_data: CancelCallback
):
    await callback_query.answer("Запрос на отмену отправлен...")
    
    identifier = (callback_data.chat_id, callback_data.message_id)
    was_cancelled = task_manager.cancel_task(identifier)
    
    if was_cancelled:
        logger.info(f"Cancellation signal sent for task {identifier}")
    else:
        logger.warning(f"Could not cancel task {identifier}. It might be already finished.")
        await callback_query.message.edit_text("Не удалось отменить. Возможно, обработка уже завершена.")