# Logging overview

Python’s [logging library](https://docs.python.org/3.7/library/logging.html) provides builtin ways to emit information about what is going on during the run of a program.

- Essentially, the steps are as follows:

1. Define a logger using `getLogger("<logger_name>")`
2. Attach handlers to that logger to define what you want to happen when a logger method emits
3. For our purposes, I’ve defined one handler that writes all logs to a tkinter textbox, and another handler that writes critical logs to a log file with a date stamp. I don’t believe we’ll need more, but if you want something else to happen with your logs, let me know!
4. Use the builtin logger methods `.debug(msg)`, `.info(msg)`, `.warning(msg)`, `.error(msg)`, or `.critical(msg)` to emit different levels of logs with a custom string msg.
   - DEBUG = Level 10
   - INFO = Level 20
   - WARNING = Level 30
   - ERROR = Level 40
   - CRITICAL = Level 50
   - We also have a custom SUCCESS log with a level of 15. To use that one, call the method `.log(15, msg)`

- Some of these steps are already set up, but documenting this in case we want to add more features.

## How to log in a certain area of the project

1. Check to see if the imports
   - `from logging import getLogger, Logger` and
   - `from modules.logging.log_utils import LOGGER_NAME`

are present at the top of the file. If not, add them.

2. Inside your class (or globally if not in a class), define a logger attribute as follows
   `logger: Logger = getLogger(LOGGER_NAME)`
   You shouldn’t need to attach any handlers or formatters; those are handled in a `log_setup` function called when the GUI renders. (if we update this, I’ll update these instructions)

3. Now use those methods as you wish to emit different logs. For example, if I wanted to log the motordict after adding or removing a motor to inspect it, I could do:

```{.python }
   def makedict(self, motnum: int, IO: IntVar):
   self.motdict[motnum-1] = IO.get()
   self.logger.debug(f"Motor statuses: " + str(self.motdict))
```

## Logging standards (just my first impulse here, let’s talk about this.)

- Use DEBUG logs when inspecting variables or troubleshooting the state of the program. No need to remove them (imo) when pushing progress. We can change the handler to filter these out and in as desired for demos and when we handoff.
  - TODO should we remove debug logs before pushing progress (to avoid clutter) or keep them to make troubleshooting easier and avoid repeatedly adding code.
- Use INFO logs to report that an operation like homing or resetting is starting and finishing, and potentially to report progress or some states of the program.
- Use WARNING logs when the user inputs parameters that are dangerously high/low, but not necessarily out of the bounds that the wavemaker can handle.
  - TODO Other warning cases?
- Use ERROR logs to reject an action from the user (bad parameters, would cause a fault, etc.), or when an action like homing or resetting times out or otherwise fails.
- Use CRITICAL logs once we get the kinks ironed out to report when our GUI crashes. Could also be used when the motors fault unexpectedly (i.e. not the user’s fault)
- Use SUCCESS logs on startup (done already), or to report that the machine is running (i.e. waves are happening) or has stopped running.

We’ll need to be careful to avoid logs getting too cluttered, as all of these logs will be sharing the textbox (right now; could change this).

Changes incoming:

- The ability to use getLogger to define loggers for different areas of the program
  - Currently, the only logger wired for use is “fluidloggers”, which has handlers attached to it that emit to the tkinter textbox and to the file for critical logs
  - My goal is to create a custom constructor, so that you can
  - Use `getLogger(<name of area of program logs are coming from>”)` Call a `log_setup(“<your logger here>)` function to attach handlers, setup formatting, etc.
  - Then, you can call your logger instead of the global one, so that messages are more localized to your area, and the users know exactly where logs are coming from.
    - We aren’t defining the logger globally and importing it into separate files because of this eventual goal.
