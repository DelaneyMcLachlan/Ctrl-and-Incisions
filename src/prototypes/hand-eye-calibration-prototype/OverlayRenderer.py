class OverlayRenderer:
    def __init__(self, vtk_overlay_window):
        self.window = vtk_overlay_window

    def render_frame(self, frame):
        """
        Display frame inside VTK window
        """
        self.window.set_video_image(frame)
        self.window.Render()

    def get_rendered_numpy(self):
        """
        Return final rendered image from the VTK scene
        """
        return self.window.convert_scene_to_numpy_array()
