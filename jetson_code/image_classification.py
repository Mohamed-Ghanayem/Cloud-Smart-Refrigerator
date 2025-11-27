import sys
import argparse
import time
import os

from jetson_inference import imageNet
from jetson_utils import videoSource, videoOutput, cudaFont, Log

# Specify the input and output URIs here
input_uri = "v4l2:///dev/video0"
output_uri = "display://0"
output_file = "recognized_item.txt"  # File to save the recognized item's name
signal_file = "recognition_terminated.txt"  # Signal file to indicate recognition termination

# load the recognition network
net = imageNet("googlenet", sys.argv)

# create video sources & outputs
input = videoSource(input_uri, argv=sys.argv)
output = videoOutput(output_uri, argv=sys.argv)
font = cudaFont()

# process frames until EOS or the user exits
start_time = time.time()
recognized_item = None
while time.time() - start_time < 10:  # Run for 5 seconds
    # capture the next image
    img = input.Capture()

    if img is None:  # timeout
        continue

    # classify the image and get the topK predictions
    predictions = net.Classify(img, topK=1)

    # Extract the recognized item's name
    if predictions:
        classID, _ = predictions[0]
        recognized_item = net.GetClassLabel(classID)

    # render the image
    output.Render(img)

    # update the title bar
    output.SetStatus("{:s} | Network {:.0f} FPS".format(net.GetNetworkName(), net.GetNetworkFPS()))

    # print out performance info
    net.PrintProfilerTimes()

    # exit on input/output EOS
    if not input.IsStreaming() or not output.IsStreaming():
        break

# Save the recognized item's name to a file
if recognized_item:
    with open(output_file, "w") as f:
        f.write(recognized_item)
        
# Create a signal file to indicate recognition termination
with open(signal_file, "w") as signal:
    signal.write("Recognition terminated")

# Close the camera window
output.glfwDestroyWindow()



