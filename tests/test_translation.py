import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from translation import Translation, Translator

from .stubs import SoundInputStub, SoundOutputStub


class TestTranslation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_translator = MagicMock(spec=Translator)
        self.stub_sound_input = SoundInputStub()
        self.stub_sound_output = SoundOutputStub()
        self.target_mapping = {'en': self.stub_sound_output}
        self.translation = Translation(
            translator=self.mock_translator,
            sound_input=self.stub_sound_input,
            target_language_mapping=self.target_mapping,
        )

    def test_init(self):
        self.assertEqual(self.translation._translator, self.mock_translator)
        self.assertEqual(self.translation._sound_input, self.stub_sound_input)
        self.assertEqual(self.translation._target_language_mapping, self.target_mapping)

    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    def test_run_success(self, mock_set_loop, mock_new_loop):
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_new_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = None

        with patch.object(self.translation, '_run_translation', return_value=AsyncMock()):
            self.translation.run()

        self.assertTrue(mock_loop.close.called)

    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    @patch('translation.LOGGER')
    def test_run_exception(self, mock_logger, mock_set_loop, mock_new_loop):
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_new_loop.return_value = mock_loop

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError('Caught runtime error')
            return None

        mock_loop.run_until_complete.side_effect = side_effect

        self.translation.run()
        self.assertTrue(mock_loop.close.called)
        mock_logger.error.assert_called()

    async def test_run_translation_cancelled(self):
        """_run_translation handles CancelledError and calls _clean_up."""
        self.mock_translator.start_translation = AsyncMock(side_effect=asyncio.CancelledError())
        with patch.object(self.translation, '_clean_up') as mock_cleanup:
            await self.translation._run_translation()
            mock_cleanup.assert_called_once()

    async def test_run_translation(self):
        """_run_translation calls start_translation on the translator."""
        self.mock_translator.start_translation = AsyncMock()
        await self.translation._run_translation()
        self.assertTrue(self.mock_translator.start_translation.called)

    def test_stop_loop_not_running(self):
        self.translation._loop = None
        self.translation.stop()
        self.assertFalse(self.translation._shutdown_event.is_set())

    @patch('asyncio.run_coroutine_threadsafe')
    def test_stop_success(self, mock_run_coro):
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_loop.is_running.return_value = True
        self.translation._loop = mock_loop

        mock_future = MagicMock()
        mock_run_coro.return_value = mock_future

        self.translation.stop()
        self.assertTrue(self.translation._shutdown_event.is_set())

    @patch('asyncio.run_coroutine_threadsafe')
    def test_stop_timeout(self, mock_run_coro):
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_loop.is_running.return_value = True
        self.translation._loop = mock_loop

        mock_future = MagicMock()
        mock_future.result.side_effect = Exception('Timeout')
        mock_run_coro.return_value = mock_future

        self.translation.stop()
        self.assertTrue(self.translation._shutdown_event.is_set())

    @patch('asyncio.wait_for', new_callable=AsyncMock)
    async def test_wait_for_main_task_graceful(self, mock_wait):
        self.translation._main_task = asyncio.Future()
        await self.translation._wait_for_main_task(1.0)
        mock_wait.assert_called_once()

    def test_clean_up(self):
        self.translation._clean_up()
        self.assertTrue(self.stub_sound_input.stop_called)
        self.assertTrue(self.stub_sound_output.stop_called)
