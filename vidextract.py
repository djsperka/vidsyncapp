#!/usr/bin/python3

import cv2
import numpy as np
from pathlib import Path
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    
if __name__ == '__main__':

    parser = ArgumentParser(description='Verify and/or extract images from vidsync', formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--file', default='', help='input filename')
    parser.add_argument('--save', default='', help='folder to place extracted images in. Will overwrite!')
   
    args = parser.parse_args()

    # verify that the files are found
    if not args.file:
        print("No filename given. Use --file.")
        exit()
        
    f = Path(args.file)
    if not f.exists():
        print("Error: input video file {:s} not found.".format(args.file))
        
    fdat = f.parent / (f.name+'.npy')
    if not fdat.exists():
        print("Error: input video file {:s} found, but accompanying data file {:s} not found.".format(str(f), fdat.name))        
   
    # Load the video and count frames
    cap = cv2.VideoCapture(f)

    # Check if video was opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        exit()

    # load io data
    iodata = np.load(str(fdat))
    print("data shape ", np.shape(iodata))

    frame_count = 0  # Initialize frame counter

    while True:
        ret, frame = cap.read()

        # Break the loop if the video ends
        if not ret:
            break

        # Save the frame as an image
        frame_filename = f"frame_{frame_count:05d}.jpg"
        #cv2.imwrite(frame_filename, frame)
        #print(f"Frame {frame_count} saved as {frame_filename}")
        
        frame_count += 1

    cap.release()
    print("Found {:d} frames.".format(frame_count))
