import action.common
import action.macro
import action.mode_control
import action.pause_resume
import action.remap
import action.response_curve
import action.text_to_speech


from gremlin.profile import UiInputType

# Mapping which indicates which action widgets have a condition
# associated with them in UI
condition_map = {
    UiInputType.JoystickAxis: [
        action.macro.MacroWidget,
        action.mode_control.CycleModesWidget,
        action.mode_control.SwitchModeWidget,
        action.mode_control.SwitchPreviousModeWidget,
        action.pause_resume.PauseActionWidget,
        action.pause_resume.ResumeActionWidget,
        action.pause_resume.TogglePauseResumeActionWidget,
        action.remap.RemapWidget,
        action.text_to_speech.TextToSpeechWidget
    ],
    UiInputType.JoystickButton: {
        action.macro.MacroWidget,
        action.mode_control.CycleModesWidget,
        action.mode_control.SwitchModeWidget,
        action.pause_resume.PauseActionWidget,
        action.pause_resume.ResumeActionWidget,
        action.pause_resume.TogglePauseResumeActionWidget,
        action.remap.RemapWidget,
        action.text_to_speech.TextToSpeechWidget
    },
    UiInputType.JoystickHat: {
        action.macro.MacroWidget,
        action.mode_control.CycleModesWidget,
        action.mode_control.SwitchModeWidget,
        action.pause_resume.PauseActionWidget,
        action.pause_resume.ResumeActionWidget,
        action.pause_resume.TogglePauseResumeActionWidget,
        action.text_to_speech.TextToSpeechWidget
    },
    UiInputType.Keyboard: {
        action.macro.MacroWidget,
        action.mode_control.CycleModesWidget,
        action.mode_control.SwitchModeWidget,
        action.pause_resume.PauseActionWidget,
        action.pause_resume.ResumeActionWidget,
        action.pause_resume.TogglePauseResumeActionWidget,
        action.remap.RemapWidget,
        action.text_to_speech.TextToSpeechWidget
    }
}

action_to_widget = {
    action.macro.Macro: action.macro.MacroWidget,
    action.mode_control.CycleModes: action.mode_control.CycleModesWidget,
    action.mode_control.SwitchMode: action.mode_control.SwitchModeWidget,
    action.mode_control.SwitchPreviousMode: action.mode_control.SwitchPreviousModeWidget,
    action.pause_resume.PauseAction: action.pause_resume.PauseActionWidget,
    action.pause_resume.ResumeAction: action.pause_resume.ResumeActionWidget,
    action.pause_resume.TogglePauseResumeAction: action.pause_resume.TogglePauseResumeActionWidget,
    action.remap.Remap: action.remap.RemapWidget,
    action.response_curve.ResponseCurve: action.response_curve.AxisResponseCurveWidget,
    action.text_to_speech.TextToSpeech: action.text_to_speech.TextToSpeechWidget
}
