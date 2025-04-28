import tkinter as tk  # tkinter: For creating the GUI (buttons, windows, dialogs)
from tkinter import filedialog, ttk, messagebox, colorchooser  # tkinter: For file dialogs, widgets, message boxes, and color picking

from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont  # PIL (Pillow): For opening, editing, and saving images (common formats like JPG, PNG, etc.)

import cv2  # OpenCV: For advanced image processing (background removal, transformations)

import numpy as np  # NumPy: For fast mathematical operations on images (matrix manipulation, filters)

import os  # os: For file and directory management (e.g., saving files, accessing paths)

from datetime import datetime  # datetime: For working with dates and times (e.g., adding timestamps to filenames)

class PhotoEditor:
    def __init__(self, root):
        self.root = root # tkinter root window instance
        self.root.title('AI Photo Editor Pro') # Set the title of the application
        self.root.geometry('1200x800') # Set initial window size
        self.root.minsize(800, 600) # Set the minimum size of the window
        
        # Image handling
        self.original_image = None  # Stores the original image (used for undo purposes)
        self.current_image = None   # Stores the current image being edited
        self.history = []           # Undo history (limited to 20 states) to allow for undo
        self.redo_stack = []        # Redo history stack to enable redo functionality
        self.tk_image = None        # Holds the Tkinter image object for displaying on canvas
        self.zoom_level = 1.0       # Default zoom level for images
        
        # UI Components
        self.configure_styles()     # Method to set up styles for UI elements like buttons and labels
        self.create_toolbar()       # Method to create the toolbar (buttons for actions like open, save, etc.)
        self.create_canvas_frame()  # Method to create the canvas for displaying images
        self.create_statusbar()     # Method to create the status bar (displays image size, zoom level, etc.)
        self.bind_shortcuts()       # Bind keyboard shortcuts for quick actions (e.g., Ctrl+Z for undo)
        
        self.show_welcome_image()   # Initialize with welcome image, Displays a default "welcome" image when the app starts


    def configure_styles(self):
        """Configure ttk styles for the application"""
        style = ttk.Style()     # Create an instance of the Style class to modify widget styles
        style.configure('TButton', padding=5)   # Set the padding for all TButtons
        style.configure('Toolbar.TFrame', background='#f0f0f0')     # Set background color for the toolbar
        style.configure('Status.TLabel', background='#f0f0f0', relief='sunken', padding=5)      # Style for status labels
        
    def create_toolbar(self):
        """Create the main toolbar with editing controls"""
        toolbar = ttk.Frame(self.root, style='Toolbar.TFrame', padding=10)      # Create a frame for the toolbar with padding
        toolbar.pack(side='top', fill='x')      # Pack the toolbar at the top of the window, stretching horizontally
        
        '''File operations'''

        file_frame = ttk.Frame(toolbar)     # Create a frame for file operations (Open and Save buttons)
        file_frame.pack(side='left', padx=5)        # Pack the file frame with padding
        ttk.Button(file_frame, text='📁 Open', command=self.open_image).pack(side='left', padx=2)  # Open button
        ttk.Button(file_frame, text='💾 Save', command=self.save_image).pack(side='left', padx=2)  # Save button
        
        ''' Edit operations'''

        edit_frame = ttk.Frame(toolbar) # Create a frame for undo and redo buttons
        edit_frame.pack(side='left', padx=5)    # Pack the edit frame with padding
        ttk.Button(edit_frame, text='↩️ Undo', command=self.undo).pack(side='left', padx=2)  # Undo button
        ttk.Button(edit_frame, text='↪️ Redo', command=self.redo).pack(side='left', padx=2)  # Redo button
        
        '''Filters section'''

        filter_frame = ttk.Frame(toolbar)   # Create a frame for filter buttons (Blur, Grayscale, Sepia(Sepia is a warm brownish tone that gives photos an "old-time" or "vintage" look), Negative)
        filter_frame.pack(side='left', padx=5)  # Pack the filter frame with padding
        ttk.Button(filter_frame, text='🔍 Blur', command=self.blur_image).pack(side='left', padx=2) # Blur button
        ttk.Button(filter_frame, text='⚫ Grayscale', command=self.apply_grayscale).pack(side='left', padx=2)   # Grayscale button
        ttk.Button(filter_frame, text='🟤 Sepia', command=self.apply_sepia).pack(side='left', padx=2)   # Sepia button
        ttk.Button(filter_frame, text='🖼️ Negative', command=self.apply_negative).pack(side='left', padx=2) # Negative button
        
        '''Advanced features section'''

        adv_frame = ttk.Frame(toolbar)  # Create a frame for advanced features buttons (Remove BG, Set BG, Reset)
        adv_frame.pack(side='left', padx=5) # Pack the advanced features frame with padding
        ttk.Button(adv_frame, text='✂️ Remove BG', command=self.remove_background).pack(side='left', padx=2)    # Remove BG button
        ttk.Button(adv_frame, text='🎨 Set BG', command=self.set_custom_background).pack(side='left', padx=2)   # Set BG button
        ttk.Button(adv_frame, text='🔄 Reset', command=self.reset_image).pack(side='left', padx=2)  # Reset button
        
        '''Adjustments section'''

        adjust_frame = ttk.Frame(toolbar)    # Create a frame for sliders (Saturation, Brightness)
        adjust_frame.pack(side='left', padx=10) # Pack the adjustments frame with padding
        
        self.sat_slider = ttk.Scale(adjust_frame, from_=0, to=200, orient='horizontal', 
                                   command=lambda v: self.change_saturation(v, save=True))   # Saturation slider
        self.sat_slider.set(100)    # Set initial value to 100
        self.sat_slider.pack(side='top', fill='x')  # Pack the slider in the frame
        ttk.Label(adjust_frame, text='Saturation').pack(side='top')  # Label for saturation slider
        
        self.bright_slider = ttk.Scale(adjust_frame, from_=0, to=200, orient='horizontal',
                                     command=lambda v: self.change_brightness(v, save=True))    # Slider for brightness
        self.bright_slider.set(100) # Set initial value to 100
        self.bright_slider.pack(side='top', fill='x')   # Pack the slider in the frame
        ttk.Label(adjust_frame, text='Brightness').pack(side='top') # Label for brightness slider

        
    def create_canvas_frame(self):
        '''Create the canvas frame with scrollbars for large images'''

        self.canvas_frame = ttk.Frame(self.root)    # Create a frame for the canvas inside the main window
        self.canvas_frame.pack(fill='both', expand=True)    # Pack the frame to fill both dimensions, allowing it to expand
    
        
        '''Horizontal and vertical scrollbars'''

        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient='horizontal')   # Horizontal scrollbar
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient='vertical') # Vertical scrollbar
        
        '''Canvas for displaying the image, with scrollbar commands linke'''

        self.canvas = tk.Canvas(
            self.canvas_frame,  # Parent frame
            bg='#333333',   # Set canvas background color to dark gray
            xscrollcommand=self.h_scroll.set,   # Connect horizontal scrollbar to canvas
            yscrollcommand=self.v_scroll.set# Connect vertical scrollbar to canvas
        )
        
        '''Grid layout to arrange canvas and scrollbars'''

        self.canvas.grid(row=0, column=0, sticky='nsew')    # Place canvas in the grid and allow it to expand in all directions
        self.v_scroll.grid(row=0, column=1, sticky='ns')     # Place vertical scrollbar below the canvas
        self.h_scroll.grid(row=1, column=0, sticky='ew')    # Place horizontal scrollbar below the canvas
    
        
        '''Configure row and column weights for resizing'''

        self.canvas_frame.rowconfigure(0, weight=1) # Make the row with the canvas flexible
        self.canvas_frame.columnconfigure(0, weight=1)  # Make the column with the canvas flexible
        
        '''Bind mouse wheel events for scrolling the canvas'''
        
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)    # Bind mouse wheel for scrolling
        self.canvas.bind('<Button-4>', lambda e: self.on_mousewheel_updown(e, up=True)) # For Linux systems, up scroll
        self.canvas.bind('<Button-5>', lambda e: self.on_mousewheel_updown(e, up=False))    # For Linux systems, down scroll
        
    def create_statusbar(self):
        '''Create the status bar at the bottom of the window'''

        self.status_bar = ttk.Frame(self.root, style='Toolbar.TFrame')  # Create a frame for the status bar
        self.status_bar.pack(side='bottom', fill='x')   # Pack the status bar at the bottom and stretch it horizontally
        
        ''' Status label to show general status of the application '''

        self.status_label = ttk.Label(
            self.status_bar,    # Parent frame
            text='Ready',   # Initial status text
            style='Status.TLabel'   # Apply predefined style
        )

        '''Image information label to show current image status (loaded or not)'''

        self.status_label.pack(side='left', fill='x', expand=True)  # Pack status label to the left and expand horizontally
        
        self.image_info_label = ttk.Label(
            self.status_bar,
            text='No image loaded',
            style='Status.TLabel'
        )
        self.image_info_label.pack(side='right')
        
    def bind_shortcuts(self):
        '''Bind keyboard shortcuts'''

        self.root.bind('<Control-z>', lambda e: self.undo())    # Bind Ctrl+Z to undo action
        self.root.bind('<Control-y>', lambda e: self.redo())    # Bind Ctrl+Y to redo action
        self.root.bind('<Control-s>', lambda e: self.save_image())  # Bind Ctrl+S to save the image
        self.root.bind('<Control-o>', lambda e: self.open_image())  # Bind Ctrl+O to open an image
        self.root.bind('<Control-r>', lambda e: self.reset_image()) # Bind Ctrl+R to reset the image
        self.root.bind('<Control-plus>', lambda e: self.zoom_image(1.1))    # Bind Ctrl+Plus to zoom in
        self.root.bind('<Control-minus>', lambda e: self.zoom_image(0.9))   # Bind Ctrl+Minus to zoom out
        self.root.bind('<Control-0>', lambda e: self.zoom_image(1.0, reset=True))   # Bind Ctrl+0 to reset zoom level
        
    def show_welcome_image(self):
        '''Show a welcome image when no image is loaded'''

        welcome_img = Image.new('RGB', (800, 600), color='#333333')  # Create a new blank image for the welcome screen
        draw = ImageDraw.Draw(welcome_img)  # Prepare to draw text on the image
        
        '''Draw welcome text'''

        try:
            font = ImageFont.truetype("arial.ttf", 40)  # Try to load a custom font
        except:
            font = ImageFont.load_default() # Use default font if custom font fails
            
        text = "AI Photo Editor\n\nOpen an image to begin editing"  # Text to display on the welcome screen
        draw.text((100, 250), text, font=font, fill="white")    # Draw the welcome text in white color
        
        self.current_image = welcome_img    # Set the welcome image as the current image
        self.tk_image = ImageTk.PhotoImage(welcome_img) # Convert the image to a format compatible with Tkinter
        self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)    # Display the image on the canvas
        
    def update_status(self, message):
        '''Update the status bar message'''

        self.status_label.config(text=message)   # Update the status message text
        self.root.update_idletasks()    # Force an update of the UI elements
        
    def update_image_info(self):
        '''Update the image information in the status bar'''

        if self.current_image:   # If an image is loaded
            width, height = self.current_image.size # Get image dimensions
            mode = self.current_image.mode  # Get the image mode (e.g., RGB, L)
            self.image_info_label.config(
                text=f"Size: {width}×{height} | Mode: {mode} | Zoom: {int(self.zoom_level*100)}%"
            )
        else:
            self.image_info_label.config(text="No image loaded")    # Show message if no image is loaded
            
    def save_history(self):
        '''Save the current image state to history'''

        if self.current_image:  # If an image is loaded
            '''Convert to RGB to ensure consistent format and copy it to avoid modifying the original'''

            img_copy = self.current_image.convert('RGB').copy()
            self.history.append(img_copy)   # Add the image state to the history stack
            
            ''' Limit the history stack to the latest 20 states'''

            if len(self.history) > 20:  
                self.history.pop(0) # Remove the oldest state if history exceeds 20 states
                
            self.redo_stack.clear() # Clear the redo stack since new history was created
            
    def open_image(self):
        '''Open an image file'''

        filetypes = [
            ('Image Files', '*.jpg *.jpeg *.png *.bmp *.gif'),
            ('All Files', '*.*')
        ]
        
        path = filedialog.askopenfilename(filetypes=filetypes)  # Open file dialog to select an image
        if path:
            try:
                self.update_status(f"Loading image: {os.path.basename(path)}...")   # Update status to loading
                self.original_image = Image.open(path).convert('RGB')   # Open and convert the image to RGB format
                self.current_image = self.original_image.copy() # Create a copy of the image for editing
                
                self.history.clear()    # Clear previous history
                self.redo_stack.clear() # Clear redo stack
                self.save_history() # Save the initial state of the image to history
                
                self.zoom_level = 1.0   # Reset zoom level
                self.show_image()   # Display the image
                self.update_status(f"Loaded: {os.path.basename(path)}") # Update status with the image file name
                self.update_image_info()    # Update image information in the status bar
                
                '''Reset sliders for saturation and brightness'''

                self.sat_slider.set(100)
                self.bright_slider.set(100)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image:\n{str(e)}") # Show error message if loading fails
                self.update_status("Ready") # Update status back to "Ready"
                
    def save_image(self):
        '''Save the current image to a file'''

        if not self.current_image:  # If there is no current image
            messagebox.showwarning("Warning", "No image to save")   # Show a warning
            return
            
        filetypes = [   # Define the file types for saving the image
            ('PNG', '*.png'),
            ('JPEG', '*.jpg'),
            ('BMP', '*.bmp'),
            ('All Files', '*.*')
        ]
        
        '''Generate default filename with timestamp in format: 'edited_YYYYMMDD_HHMMSS.png'''

        default_name = f"edited_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        path = filedialog.asksaveasfilename(    # Open save file dialog
            defaultextension='.png',    # Default extension for saved files
            filetypes=filetypes,    # Allowed file types
            initialfile=default_name    # Default file name
        )
        
        if path:    # If a path is selected
            try:
                self.update_status(f"Saving image...")  # Update status to indicate image is being saved
                self.current_image.save(path)   # Save the current image to the selected path
                self.update_status(f"Saved: {os.path.basename(path)}")  # Update status with saved file name
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{str(e)}")   # Show error message
                self.update_status("Ready") # Reset status to "Ready"
                
    def show_image(self):
        '''Display the current image on canvas'''

        if self.current_image:  # If there is a current image
            '''Calculate dimensions based on zoom level'''

            width = int(self.current_image.width * self.zoom_level)
            height = int(self.current_image.height * self.zoom_level)
            
            '''Resize the image to the new dimensions'''

            resized = self.current_image.resize((width, height), Image.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized) # Convert the resized image to Tkinter format
            
            ''' Update the canvas to display the resized image'''

            self.canvas.delete('all')   # Remove any existing images from the canvas
            self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)    # Add the resized image to the canvas
            
            ''' Update the canvas scroll region based on the new image size'''

            self.canvas.config(scrollregion=self.canvas.bbox('all'))
            
            '''Update image info in the status bar'''

            self.update_image_info()
            
    def zoom_image(self, factor, reset=False):
        '''Zoom in/out of the image'''

        if not self.current_image:  # If there is no current image
            return
            
        if reset:
            self.zoom_level = 1.0   # If reset flag is True, set zoom level back to 1.0
        else:
            self.zoom_level *= factor
            self.zoom_level = max(0.1, min(self.zoom_level, 10.0))  # Limit zoom range
            
        self.show_image()
        
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling (Windows/Mac)"""
        if event.state & 0x1:  # Shift key pressed - horizontal scroll
            self.canvas.xview_scroll(-1 * (event.delta // 120), 'units')
        else:  # Vertical scroll
            self.canvas.yview_scroll(-1 * (event.delta // 120), 'units')
            
    def on_mousewheel_updown(self, event, up):
        """Handle mouse wheel scrolling (Linux)"""
        if event.state & 0x1:  # Shift key pressed - horizontal scroll
            direction = -1 if up else 1
            self.canvas.xview_scroll(direction, 'units')
        else:  # Vertical scroll
            direction = -1 if up else 1
            self.canvas.yview_scroll(direction, 'units')
            
    def undo(self):
        '''Undo the last operation'''

        if len(self.history) > 1:  # Ensure there's at least the original image in history
            self.redo_stack.append(self.history.pop())  # Add the last operation to redo stack
            self.current_image = self.history[-1].copy()    # Restore the last saved image
            self.show_image()    # Show the restored image
            self.update_status("Undo last operation")   # Update status to indicate undo action
            
    def redo(self):
        '''Redo the last undone operation'''

        if self.redo_stack: # If there are undone operations to redo
            self.save_history() # Save the current state to history
            self.current_image = self.redo_stack.pop().copy()   # Restore the last undone operation
            self.show_image()   # Show the restored image
            self.update_status("Redo last operation")   # Update status to indicate redo action
            
    def reset_image(self):
        '''Reset image to original state'''

        if self.original_image: # Ensure there's an original image to reset to
            self.save_history() # Save the current state to history
            self.current_image = self.original_image.copy() # Reset to the original image
            self.zoom_level = 1.0   # Reset zoom level
            self.show_image()   # Show the original image
            self.update_status("Image reset to original")   # Update status to indicate reset

            
            '''Reset the sliders for saturation and brightness to default (100)'''

            self.sat_slider.set(100)
            self.bright_slider.set(100)
            
    def apply_filter(self, filter_func, description):
        ''' Apply a filter function to the image'''

        if not self.current_image:  # Ensure there's an image to apply the filter to 
            return
            
        self.save_history() # Save the current state before applying the filter
        self.current_image = filter_func(self.current_image)    # Apply the filter
        self.show_image()   # Show the updated image
        self.update_status(f"Applied: {description}")   # Update status to indicate filter applied
        
    def blur_image(self):
        '''Apply Gaussian blur to the image'''

        if not self.current_image:  # Ensure there's an image to blur
            return
            
        self.save_history() # Save the current state before applying the blur
        
        '''Create a dialog for blur level selection'''

        blur_dialog = tk.Toplevel(self.root)
        blur_dialog.title("Select Blur Level")
        blur_dialog.transient(self.root)    # Keep the dialog on top of the main window
        
        ttk.Label(blur_dialog, text="Blur Radius:").pack(pady=5)    # Label for blur level
        

        '''Create a scale widget for selecting blur level'''

        blur_level = tk.IntVar(value=2)
        ttk.Scale(blur_dialog, from_=1, to=10, variable=blur_level, orient='horizontal').pack(padx=10, pady=5)
        
        def apply_blur(): # Apply the selected blur level
            self.current_image = self.current_image.filter(
                ImageFilter.GaussianBlur(blur_level.get())  # Apply Gaussian blur
            )
            self.show_image()   # Show the blurred image
            blur_dialog.destroy()   # Close the dialog
            self.update_status(f"Applied: Gaussian Blur (radius={blur_level.get()})")     # Update status
            
        ttk.Button(blur_dialog, text="Apply", command=apply_blur).pack(pady=10) # Button to apply blur
        
    def apply_grayscale(self):
        '''Convert image to grayscale'''

        self.apply_filter(
            lambda img: ImageOps.grayscale(img).convert('RGB'), # Convert image to grayscale and back to RGB
            "Grayscale" # Filter description
        )
        
    def apply_negative(self):
        '''Invert image colors'''

        self.apply_filter(  # Invert the colors of the image
            ImageOps.invert,    # Invert the colors of the image
            "Negative"  # Filter description
        )
        
    def apply_sepia(self):
        '''Apply sepia tone to the image'''

        def sepia_filter(img):  
            img = np.array(img) # Convert image to numpy array
            sepia_matrix = np.array([   # Define sepia tone transformation matrix
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            sepia_img = cv2.transform(img, sepia_matrix)    # Apply the transformation
            sepia_img = np.clip(sepia_img, 0, 255)  # Clip the values to valid pixel range
            return Image.fromarray(sepia_img.astype('uint8'))   # Convert back to an image
            
        self.apply_filter(sepia_filter, "Sepia Tone")   # Apply the sepia filter
        
    def change_saturation(self, value, save=False):
        '''Adjust image saturation'''

        if not self.current_image:  # Ensure there's an image to adjust
            return
            
        if save:    # Save the history if required
            self.save_history()
            
        factor = float(value) / 100 # Convert the slider value to a factor
        enhancer = ImageEnhance.Color(self.current_image)
        self.current_image = enhancer.enhance(factor)
        self.show_image()
        
    def change_brightness(self, value, save=False):
        """Adjust image brightness"""
        if not self.current_image:
            return
            
        if save:
            self.save_history()
            
        factor = float(value) / 100
        enhancer = ImageEnhance.Brightness(self.current_image)  # Create an enhancer for color
        self.current_image = enhancer.enhance(factor)   # Apply the saturation change
        self.show_image()   # Show the updated image
        
    def remove_background(self):
        '''Remove image background using grabCut algorithm'''

        if not self.current_image:  # Check if there's a current image loaded
            return
            
        self.save_history() # Save the current state for undo/redo functionality
        self.update_status("Removing background... (this may take a moment)")   # Inform the user that the process is ongoing
        
        try:
            '''Convert to OpenCV format'''

            img_cv = cv2.cvtColor(np.array(self.current_image), cv2.COLOR_RGB2BGR)
            
            '''Initialize mask and background/foreground models used in grabCut'''

            mask = np.zeros(img_cv.shape[:2], np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            '''Define the rectangle to initialize the grabCut algorithm (10px margin from edges)'''

            h, w = img_cv.shape[:2] # Get image dimensions (height and width)
            rect = (10, 10, w-20, h-20) # Define rectangl
            
            '''Apply grabCut algorithm with the initial rectangle, models, and mask'''

            cv2.grabCut(img_cv, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            '''Create a final mask: foreground pixels will be marked as 1, others as 0'''

            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            '''Apply the mask to the image to remove the background (set background to black)'''

            result = img_cv * mask2[:, :, np.newaxis]
            
            '''Convert the result to RGBA format to add transparency (alpha channel)'''

            rgba = cv2.cvtColor(result, cv2.COLOR_BGR2RGBA)
            rgba[:, :, 3] = mask2 * 255
            
            self.current_image = Image.fromarray(rgba)
            self.show_image()
            self.update_status("Background removed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove background:\n{str(e)}")
            self.update_status("Ready")
            
    def set_custom_background(self):
        '''Set a custom background color for transparent images
        Check if the current image exists and is in 'RGBA' mode (to support transparency)
        '''

        if not self.current_image or self.current_image.mode != 'RGBA':
            messagebox.showinfo("Info", "Please remove background first to make it transparent.")   # Prompt user
            return
            
        color = colorchooser.askcolor(title="Select Background Color")
        if color[1]:  # color[1] is the hex string
            bg_color = color[1]
            
            '''Create solid background'''

            bg_img = Image.new('RGBA', self.current_image.size, bg_color)
            
            self.save_history() # Save the current image state for undo/redo functionality
            
            '''Composite with current image'''

            self.current_image = Image.alpha_composite(bg_img, self.current_image)
            self.show_image()   # Display the modified image
            self.update_status(f"Background set to {bg_color}") # Inform the user about the new background color

if __name__ == '__main__':  # This checks if the script is being run directly (not imported from somewhere else)
    
    root = tk.Tk()  # Create the main window for the app using tkinter (tk)

    try:
        
        
        root.tk.call('source', 'azure/azure.tcl')   # 'source' loads the theme file (azure.tcl)
        
        root.tk.call('set_theme', 'dark')   # 'set_theme' switches the appearance to dark mode
    except:
        
        pass    # If there is any error (like if the theme file isn't found), just ignore it and continue

    
    app = PhotoEditor(root) # Create an instance of the PhotoEditor application, passing the main window (root) to it

    
    root.mainloop() # Start the app's event loop — this keeps the window open and waits for user actions

 