'''
Updated by Sicheng Wang for better performance and functionality

GUI developed by Jasper Christie, Marc Lewis, Chelsea Rowe and Ezri White for use by UNC-Fluids Lab.

Original GUI created by Raphael Provosty(rprovosty@gmail.com) and Schuyler Moss for use by UNC-Fluids Lab.

Uses the pylogix library originally created by Burt Peterson
Updated and maintained by Dustin Roeder (dmroeder@gmail.com) 
https://github.com/dmroeder/pylogix
'''

from View import View
from Model import Model


def main() -> None:
    model: Model = Model()
    if model.CONNECTED:
        model.motor_off()
    view: View = View(model)


if __name__ == "__main__":
    main()
