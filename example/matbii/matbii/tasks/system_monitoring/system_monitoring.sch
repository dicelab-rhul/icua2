# TODO schedules that use 0 (or very small values) can cause problems for the browser as the XML update is schedule before the initial sensing of the SVG data. This could be fixed by having the schedule agent wait for the first cycle to finish before starting the schedule...

####  System Monitoring Task Schedule ####

# this makes the lights turn to their unacceptable state "off"
off_light(1) @ [uniform(3,10)]:*    # this means failure for light 1
on_light(2) @ [uniform(3,10)]:*     # this means failure for light 2
# toggle_light(X) is also an option

# this randomly moves the sliders (up/down by 1)
perturb_slider(1) @ [uniform(2,5)]:*
perturb_slider(2) @ [uniform(2,5)]:*
perturb_slider(3) @ [uniform(2,5)]:*
perturb_slider(4) @ [uniform(2,5)]:*