# This Python file uses the following encoding: utf-8
import sys

from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.uic import loadUi
from typing import Union
import re
from dotenv import load_dotenv
from os import getenv
import openai
from time import sleep

class Calculator(QMainWindow):
    def __init__(self):
        super(Calculator, self).__init__()
        load_dotenv()
        self.next_input_is_decimal: bool = False
        self.a_number: str = ""
        self.b_number: str = ""
        self.operator: str = ""
        self.player: Union[QMediaPlayer, None] = None
        self.audio_output: Union[QAudioOutput, None] = None
        # 0 => First number, 1 => Second Number, 2 => Result mode
        self.current_step: int = 0
        loadUi("form.ui", self)
        self.register_click_actions()
        self.init_player()

    # noinspection PyUnresolvedReferences
    def send_operation(self, operator: str) -> None:
        if "" == self.a_number:
            self.a_number = 0
        if "" == self.b_number:
            self.b_number = 0
        if "" == operator:
            error: QMessageBox = QMessageBox(self)
            error.setWindowTitle("Operation not valid!")
            error.setText("You must insert an operator to continue")
            error.exec()
            self.clear_screen()
            return

        openai.api_key = getenv('CHAT_GPT_TOKEN')
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": f"Do not explain it. In case of error, just say '[ERROR] - ' and a very short reason. "
                               f"Solve this:"
                               f"{self.a_number}{operator}{self.b_number}"
                }
            ]
        )
        try:
            response = response.choices[0].message.content
            if re.search(r"\[ERROR] -", response):
                error: QMessageBox = QMessageBox(self)
                error.setWindowTitle("Operation not valid!")
                error.setText(response)
                error.exec()
                self.clear_screen()
                return
            self.clear_screen()
            response = self.prepare_response(response)
            self.calculatorDisplay.display(response)
        except: # Generic Exception, I didn't have time to read the entire OPENAPI Doc
            self.clear_screen()
            error: QMessageBox = QMessageBox(self)
            error.setWindowTitle("Error!")
            error.setText("OpenAPI is not available")
            error.exec()
            self.clear_screen()

    def prepare_response(self, value: str) -> str:
        try:
            if 10 < len(value):
                return str("{:.2e}".format(float(value)).upper().replace("E+", "E"))
            return value
        except:
            return value

    def init_player(self) -> None:
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile("./assets/cat-meow.mp3"))
        self.audio_output.setVolume(100.0)

    def play_sound(self) -> None:
        if None is self.player:
            return
        self.player.stop()
        self.player.setPosition(0)
        self.player.play()

    # noinspection PyUnresolvedReferences
    def register_click_actions(self) -> None:
        self.key0.clicked.connect(lambda: self.keyboard_event_handler(0))
        self.key1.clicked.connect(lambda: self.keyboard_event_handler(1))
        self.key2.clicked.connect(lambda: self.keyboard_event_handler(2))
        self.key3.clicked.connect(lambda: self.keyboard_event_handler(3))
        self.key4.clicked.connect(lambda: self.keyboard_event_handler(4))
        self.key5.clicked.connect(lambda: self.keyboard_event_handler(5))
        self.key6.clicked.connect(lambda: self.keyboard_event_handler(6))
        self.key7.clicked.connect(lambda: self.keyboard_event_handler(7))
        self.key8.clicked.connect(lambda: self.keyboard_event_handler(8))
        self.key9.clicked.connect(lambda: self.keyboard_event_handler(9))
        self.keyDot.clicked.connect(lambda: self.keyboard_event_handler('.'))
        self.keyClr.clicked.connect(lambda: self.clear_screen())
        self.keyMul.clicked.connect(lambda: self.set_operator("*"))
        self.keyAdd.clicked.connect(lambda: self.set_operator("+"))
        self.keySub.clicked.connect(lambda: self.set_operator("-"))
        self.keyDiv.clicked.connect(lambda: self.set_operator("/"))
        self.keyEqu.clicked.connect(lambda: self.handle_equal_key_event())

    def set_operator(self, operator: str) -> None:
        self.operator = operator
        self.current_step = 1

    def handle_equal_key_event(self) -> None:
        if "" == self.operator:
            self.current_step = 3
            if "" != self.b_number:
                self.calculatorDisplay.display(0)
            elif "" != self.a_number:
                self.calculatorDisplay.display(self.a_number)
            else:
                self.calculatorDisplay.display(0)
            return
        self.send_operation(self.operator)

    def set_current_value(self, value: str) -> None:
        if 1 == self.current_step:
            self.b_number = value
        else:
            self.a_number = value
        self._update_screen(value)

    def get_current_value(self) -> str:
        if 0 == self.current_step:
            return self.a_number
        if 1 == self.current_step:
            return self.b_number
        # Reset current "state"
        self.clear_screen()
        return self.a_number

    # noinspection PyUnresolvedReferences
    def clear_screen(self) -> None:
        self.calculatorDisplay.display(0)
        self.a_number = self.b_number = self.operator = ""
        self.current_step = 0
        self.next_input_is_decimal = False

    # noinspection PyUnresolvedReferences
    def keyboard_event_handler(self, key: Union[int, str]) -> None:
        display_value: str = self.get_current_value()
        if 10 == len(display_value):
            error: QMessageBox = QMessageBox(self)
            error.setWindowTitle("Error!")
            error.setText("Sorry, no more than 10 digits are allowed")
            error.exec()
            return
        self.play_sound()
        if "." == key:
            if re.search(r"\d+\.", display_value):
                # Just ignore the event
                return
            self.next_input_is_decimal = True
            return
        if self.next_input_is_decimal:
            self.next_input_is_decimal = False
            if "" == display_value:
                display_value = f"0.{key}"
                self.set_current_value(display_value)
                return
            self.set_current_value(f"{display_value}.{key}")
            return
        self.set_current_value(f"{display_value}{key}")

    # noinspection PyUnresolvedReferences
    def _update_screen(self, value: Union[str, float]) -> None:
        self.calculatorDisplay.display(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Calculator()
    widget.setMaximumWidth(widget.width())
    widget.setMinimumWidth(widget.width())
    widget.setMaximumHeight(widget.height())
    widget.setMinimumHeight(widget.height())
    widget.show()
    sys.exit(app.exec())
