from gui.main_window import MainWindow
from gui import globals
from main.test import create_test_circuit

import sys

from PyQt5.QtWidgets import QApplication


def main():
	sys._excepthook = sys.excepthook
	def my_exception_hook(exctype, value, traceback):
		print(exctype, value, traceback)
		sys._excepthook(exctype, value, traceback)
		sys.exit(1)
	sys.excepthook = my_exception_hook

	globals.circuit = create_test_circuit()
	app = QApplication(sys.argv)
	w = MainWindow()
	w.show()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()
