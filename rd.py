# RenderDoc Python console, powered by python 3.6.4.
# https://www.python.org/ftp/python/3.6.4/python-3.6.4-amd64.exe

# The 'pyrenderdoc' object is the current CaptureContext instance.
# The 'renderdoc' and 'qrenderdoc' modules are available.
# Documentation is available: https://renderdoc.org/docs/python_api/index.html

# HTML report generation

# https://renderdoc.org/docs/python_api/renderdoc/index.html

# cpu side fetch
# C:\svn_pool\renderdoc\renderdoc\api\replay\renderdoc_replay.h
# C:\svn_pool\renderdoc\renderdoc\api\replay\data_types.h
# C:\svn_pool\renderdoc\renderdoc\api\replay\replay_enums.h

# replay the trace to get state, needs gpu
# C:\svn_pool\renderdoc\renderdoc\replay\replay_controller.h

# TODO
# [] Add a json layer for generate_raw_data, separate raw_data and controller
# [] Add resource manager, and export to disk

import os
import sys
import math
from pathlib import Path, WindowsPath
import pprint
from datetime import datetime
from collections import defaultdict, OrderedDict
from enum import Enum, auto
import subprocess
import struct
import json

sys.path.append('../renderdoc/x64/Development/pymodules')
os.environ["PATH"] += os.path.abspath('../renderdoc/x64/Development')

import renderdoc as rd

# config <----> %APPDATA%/rd.json
config = {
    'MINIMALIST' : False,  # Enable full mode
    'WRITE_MALIOC' : True,  # Enable Mali offline compiler analysis
    'WRITE_CONST_BUFFER' : True,  # Enable constant buffer writing
    'WRITE_PIPELINE' : True,
    'WRITE_COLOR_BUFFER' : True,  # Enable color buffer writing
    'WRITE_TEXTURE' : True,  # Enable texture writing
    'WRITE_DEPTH_BUFFER' : True,  # Enable depth buffer writing
    'WRITE_PSO_DAG' : True,
    'WRITE_SINGLE_COLOR' : True,
    'WRITE_ALL_DRAWS' : True,
    'IMAGE_COMPRESSION' : True,  # Enable image compression
    'MAX_IMAGE_SIZE' : 256,  # Maximum image size
    'JPEG_QUALITY' : 85,  # JPEG compression quality (0-100)
}

api_full_log = None
api_short_log = None
API_TYPE = None # GraphicsAPI
IMG_EXT = 'jpg'

def getSafeName(name):
    if name[0] == '_':
        name = name[1:]
    if len(name) > 100:
        name = name[0: 99]

    invalid_chars = r'\/:*?"<>|#() -{}.'
    for c in invalid_chars:
        name = name.replace(c, '_')
    name = name.replace('__', '_')
    return name

class ShaderStage(Enum):
    VS = 0
    HS = auto()
    DS = auto()
    GS = auto()
    PS = auto()
    CS = auto()

class GLChunk(Enum):
    Dummy = 0

    # C:\svn_pool\renderdoc\renderdoc\core\core.h
    DriverInit = 1
    InitialContentsList = auto()
    InitialContents = auto
    CaptureBegin = auto
    CaptureScope = auto
    CaptureEnd = 6

    FirstDriverChunk = 1000

    # C:\svn_pool\renderdoc\renderdoc\driver\gl\gl_common.h
    MakeContextCurrent = auto()
    vrapi_CreateTextureSwapChain = auto()
    vrapi_CreateTextureSwapChain2 = auto()
    glBindTexture = auto()
    glBlendFunc = auto()
    glClear = auto()
    glClearColor = auto()
    glClearDepth = auto()
    glClearStencil = auto()
    glColorMask = auto()
    glCullFace = auto()
    glDepthFunc = auto()
    glDepthMask = auto()
    glDepthRange = auto()
    glStencilFunc = auto()
    glStencilMask = auto()
    glStencilOp = auto()
    glDisable = auto()
    glDrawBuffer = auto()
    glDrawElements = auto()
    glDrawArrays = auto()
    glEnable = auto()
    glFlush = auto()
    glFinish = auto()
    glFrontFace = auto()
    glGenTextures = auto()
    glDeleteTextures = auto()
    glIsEnabled = auto()
    glIsTexture = auto()
    glGetError = auto()
    glGetTexLevelParameteriv = auto()
    glGetTexLevelParameterfv = auto()
    glGetTexParameterfv = auto()
    glGetTexParameteriv = auto()
    glGetTexImage = auto()
    glGetBooleanv = auto()
    glGetFloatv = auto()
    glGetDoublev = auto()
    glGetIntegerv = auto()
    glGetPointerv = auto()
    glGetPointervKHR = auto()
    glGetString = auto()
    glHint = auto()
    glLogicOp = auto()
    glPixelStorei = auto()
    glPixelStoref = auto()
    glPolygonMode = auto()
    glPolygonOffset = auto()
    glPointSize = auto()
    glLineWidth = auto()
    glReadPixels = auto()
    glReadBuffer = auto()
    glScissor = auto()
    glTexImage1D = auto()
    glTexImage2D = auto()
    glTexSubImage1D = auto()
    glTexSubImage2D = auto()
    glCopyTexImage1D = auto()
    glCopyTexImage2D = auto()
    glCopyTexSubImage1D = auto()
    glCopyTexSubImage2D = auto()
    glTexParameterf = auto()
    glTexParameterfv = auto()
    glTexParameteri = auto()
    glTexParameteriv = auto()
    glViewport = auto()
    glActiveTexture = auto()
    glActiveTextureARB = auto()
    glTexStorage1D = auto()
    glTexStorage1DEXT = auto()
    glTexStorage2D = auto()
    glTexStorage2DEXT = auto()
    glTexStorage3D = auto()
    glTexStorage3DEXT = auto()
    glTexStorage2DMultisample = auto()
    glTexStorage3DMultisample = auto()
    glTexStorage3DMultisampleOES = auto()
    glTexImage3D = auto()
    glTexImage3DEXT = auto()
    glTexImage3DOES = auto()
    glTexSubImage3D = auto()
    glTexSubImage3DOES = auto()
    glTexBuffer = auto()
    glTexBufferARB = auto()
    glTexBufferEXT = auto()
    glTexBufferOES = auto()
    glTexImage2DMultisample = auto()
    glTexImage3DMultisample = auto()
    glCompressedTexImage1D = auto()
    glCompressedTexImage1DARB = auto()
    glCompressedTexImage2D = auto()
    glCompressedTexImage2DARB = auto()
    glCompressedTexImage3D = auto()
    glCompressedTexImage3DARB = auto()
    glCompressedTexImage3DOES = auto()
    glCompressedTexSubImage1D = auto()
    glCompressedTexSubImage1DARB = auto()
    glCompressedTexSubImage2D = auto()
    glCompressedTexSubImage2DARB = auto()
    glCompressedTexSubImage3D = auto()
    glCompressedTexSubImage3DARB = auto()
    glCompressedTexSubImage3DOES = auto()
    glTexBufferRange = auto()
    glTexBufferRangeEXT = auto()
    glTexBufferRangeOES = auto()
    glTextureView = auto()
    glTextureViewEXT = auto()
    glTextureViewOES = auto()
    glTexParameterIiv = auto()
    glTexParameterIivEXT = auto()
    glTexParameterIivOES = auto()
    glTexParameterIuiv = auto()
    glTexParameterIuivEXT = auto()
    glTexParameterIuivOES = auto()
    glGenerateMipmap = auto()
    glGenerateMipmapEXT = auto()
    glCopyImageSubData = auto()
    glCopyImageSubDataEXT = auto()
    glCopyImageSubDataOES = auto()
    glCopyTexSubImage3D = auto()
    glCopyTexSubImage3DOES = auto()
    glGetInternalformativ = auto()
    glGetInternalformati64v = auto()
    glGetBufferParameteriv = auto()
    glGetBufferParameterivARB = auto()
    glGetBufferParameteri64v = auto()
    glGetBufferPointerv = auto()
    glGetBufferPointervARB = auto()
    glGetBufferPointervOES = auto()
    glGetFragDataIndex = auto()
    glGetFragDataLocation = auto()
    glGetFragDataLocationEXT = auto()
    glGetStringi = auto()
    glGetBooleani_v = auto()
    glGetIntegeri_v = auto()
    glGetFloati_v = auto()
    glGetFloati_vEXT = auto()
    glGetFloati_vOES = auto()
    glGetFloati_vNV = auto()
    glGetDoublei_v = auto()
    glGetDoublei_vEXT = auto()
    glGetInteger64i_v = auto()
    glGetInteger64v = auto()
    glGetShaderiv = auto()
    glGetShaderInfoLog = auto()
    glGetShaderPrecisionFormat = auto()
    glGetShaderSource = auto()
    glGetAttachedShaders = auto()
    glGetProgramiv = auto()
    glGetProgramInfoLog = auto()
    glGetProgramInterfaceiv = auto()
    glGetProgramResourceIndex = auto()
    glGetProgramResourceiv = auto()
    glGetProgramResourceName = auto()
    glGetProgramPipelineiv = auto()
    glGetProgramPipelineivEXT = auto()
    glGetProgramPipelineInfoLog = auto()
    glGetProgramPipelineInfoLogEXT = auto()
    glGetProgramBinary = auto()
    glGetProgramResourceLocation = auto()
    glGetProgramResourceLocationIndex = auto()
    glGetProgramStageiv = auto()
    glGetGraphicsResetStatus = auto()
    glGetGraphicsResetStatusARB = auto()
    glGetGraphicsResetStatusEXT = auto()
    glGetObjectLabel = auto()
    glGetObjectLabelKHR = auto()
    glGetObjectLabelEXT = auto()
    glGetObjectPtrLabel = auto()
    glGetObjectPtrLabelKHR = auto()
    glGetDebugMessageLog = auto()
    glGetDebugMessageLogARB = auto()
    glGetDebugMessageLogKHR = auto()
    glGetFramebufferAttachmentParameteriv = auto()
    glGetFramebufferAttachmentParameterivEXT = auto()
    glGetFramebufferParameteriv = auto()
    glGetRenderbufferParameteriv = auto()
    glGetRenderbufferParameterivEXT = auto()
    glGetMultisamplefv = auto()
    glGetQueryIndexediv = auto()
    glGetQueryObjectui64v = auto()
    glGetQueryObjectui64vEXT = auto()
    glGetQueryObjectuiv = auto()
    glGetQueryObjectuivARB = auto()
    glGetQueryObjectuivEXT = auto()
    glGetQueryObjecti64v = auto()
    glGetQueryObjecti64vEXT = auto()
    glGetQueryObjectiv = auto()
    glGetQueryObjectivARB = auto()
    glGetQueryObjectivEXT = auto()
    glGetQueryiv = auto()
    glGetQueryivARB = auto()
    glGetQueryivEXT = auto()
    glGetSynciv = auto()
    glGetBufferSubData = auto()
    glGetBufferSubDataARB = auto()
    glGetVertexAttribiv = auto()
    glGetVertexAttribPointerv = auto()
    glGetCompressedTexImage = auto()
    glGetCompressedTexImageARB = auto()
    glGetnCompressedTexImage = auto()
    glGetnCompressedTexImageARB = auto()
    glGetnTexImage = auto()
    glGetnTexImageARB = auto()
    glGetTexParameterIiv = auto()
    glGetTexParameterIivEXT = auto()
    glGetTexParameterIivOES = auto()
    glGetTexParameterIuiv = auto()
    glGetTexParameterIuivEXT = auto()
    glGetTexParameterIuivOES = auto()
    glClampColor = auto()
    glClampColorARB = auto()
    glReadnPixels = auto()
    glReadnPixelsARB = auto()
    glReadnPixelsEXT = auto()
    glGetSamplerParameterIiv = auto()
    glGetSamplerParameterIivEXT = auto()
    glGetSamplerParameterIivOES = auto()
    glGetSamplerParameterIuiv = auto()
    glGetSamplerParameterIuivEXT = auto()
    glGetSamplerParameterIuivOES = auto()
    glGetSamplerParameterfv = auto()
    glGetSamplerParameteriv = auto()
    glGetTransformFeedbackVarying = auto()
    glGetTransformFeedbackVaryingEXT = auto()
    glGetSubroutineIndex = auto()
    glGetSubroutineUniformLocation = auto()
    glGetActiveAtomicCounterBufferiv = auto()
    glGetActiveSubroutineName = auto()
    glGetActiveSubroutineUniformName = auto()
    glGetActiveSubroutineUniformiv = auto()
    glGetUniformLocation = auto()
    glGetUniformIndices = auto()
    glGetUniformSubroutineuiv = auto()
    glGetUniformBlockIndex = auto()
    glGetAttribLocation = auto()
    glGetActiveUniform = auto()
    glGetActiveUniformName = auto()
    glGetActiveUniformBlockName = auto()
    glGetActiveUniformBlockiv = auto()
    glGetActiveUniformsiv = auto()
    glGetActiveAttrib = auto()
    glGetUniformfv = auto()
    glGetUniformiv = auto()
    glGetUniformuiv = auto()
    glGetUniformuivEXT = auto()
    glGetUniformdv = auto()
    glGetnUniformdv = auto()
    glGetnUniformdvARB = auto()
    glGetnUniformfv = auto()
    glGetnUniformfvARB = auto()
    glGetnUniformfvEXT = auto()
    glGetnUniformiv = auto()
    glGetnUniformivARB = auto()
    glGetnUniformivEXT = auto()
    glGetnUniformuiv = auto()
    glGetnUniformuivARB = auto()
    glGetVertexAttribIiv = auto()
    glGetVertexAttribIivEXT = auto()
    glGetVertexAttribIuiv = auto()
    glGetVertexAttribIuivEXT = auto()
    glGetVertexAttribLdv = auto()
    glGetVertexAttribLdvEXT = auto()
    glGetVertexAttribdv = auto()
    glGetVertexAttribfv = auto()
    glCheckFramebufferStatus = auto()
    glCheckFramebufferStatusEXT = auto()
    glBlendColor = auto()
    glBlendColorEXT = auto()
    glBlendFunci = auto()
    glBlendFunciARB = auto()
    glBlendFunciEXT = auto()
    glBlendFunciOES = auto()
    glBlendFuncSeparate = auto()
    glBlendFuncSeparateARB = auto()
    glBlendFuncSeparatei = auto()
    glBlendFuncSeparateiARB = auto()
    glBlendFuncSeparateiEXT = auto()
    glBlendFuncSeparateiOES = auto()
    glBlendEquation = auto()
    glBlendEquationEXT = auto()
    glBlendEquationi = auto()
    glBlendEquationiARB = auto()
    glBlendEquationiEXT = auto()
    glBlendEquationiOES = auto()
    glBlendEquationSeparate = auto()
    glBlendEquationSeparateARB = auto()
    glBlendEquationSeparateEXT = auto()
    glBlendEquationSeparatei = auto()
    glBlendEquationSeparateiARB = auto()
    glBlendEquationSeparateiEXT = auto()
    glBlendEquationSeparateiOES = auto()
    glBlendBarrierKHR = auto()
    glStencilFuncSeparate = auto()
    glStencilMaskSeparate = auto()
    glStencilOpSeparate = auto()
    glColorMaski = auto()
    glColorMaskiEXT = auto()
    glColorMaskIndexedEXT = auto()
    glColorMaskiOES = auto()
    glSampleMaski = auto()
    glSampleCoverage = auto()
    glSampleCoverageARB = auto()
    glMinSampleShading = auto()
    glMinSampleShadingARB = auto()
    glMinSampleShadingOES = auto()
    glDepthRangef = auto()
    glDepthRangeIndexed = auto()
    glDepthRangeArrayv = auto()
    glClipControl = auto()
    glProvokingVertex = auto()
    glProvokingVertexEXT = auto()
    glPrimitiveRestartIndex = auto()
    glCreateShader = auto()
    glDeleteShader = auto()
    glShaderSource = auto()
    glCompileShader = auto()
    glCreateShaderProgramv = auto()
    glCreateShaderProgramvEXT = auto()
    glCreateProgram = auto()
    glDeleteProgram = auto()
    glAttachShader = auto()
    glDetachShader = auto()
    glReleaseShaderCompiler = auto()
    glLinkProgram = auto()
    glProgramParameteri = auto()
    glProgramParameteriARB = auto()
    glProgramParameteriEXT = auto()
    glUseProgram = auto()
    glShaderBinary = auto()
    glProgramBinary = auto()
    glUseProgramStages = auto()
    glUseProgramStagesEXT = auto()
    glValidateProgram = auto()
    glGenProgramPipelines = auto()
    glGenProgramPipelinesEXT = auto()
    glBindProgramPipeline = auto()
    glBindProgramPipelineEXT = auto()
    glActiveShaderProgram = auto()
    glActiveShaderProgramEXT = auto()
    glDeleteProgramPipelines = auto()
    glDeleteProgramPipelinesEXT = auto()
    glValidateProgramPipeline = auto()
    glValidateProgramPipelineEXT = auto()
    glDebugMessageCallback = auto()
    glDebugMessageCallbackARB = auto()
    glDebugMessageCallbackKHR = auto()
    glDebugMessageControl = auto()
    glDebugMessageControlARB = auto()
    glDebugMessageControlKHR = auto()
    glDebugMessageInsert = auto()
    glDebugMessageInsertARB = auto()
    glDebugMessageInsertKHR = auto()
    glPushDebugGroup = auto()
    glPushDebugGroupKHR = auto()
    glPopDebugGroup = auto()
    glPopDebugGroupKHR = auto()
    glObjectLabel = auto()
    glObjectLabelKHR = auto()
    glLabelObjectEXT = auto()
    glObjectPtrLabel = auto()
    glObjectPtrLabelKHR = auto()
    glEnablei = auto()
    glEnableiEXT = auto()
    glEnableIndexedEXT = auto()
    glEnableiOES = auto()
    glEnableiNV = auto()
    glDisablei = auto()
    glDisableiEXT = auto()
    glDisableIndexedEXT = auto()
    glDisableiOES = auto()
    glDisableiNV = auto()
    glIsEnabledi = auto()
    glIsEnablediEXT = auto()
    glIsEnabledIndexedEXT = auto()
    glIsEnablediOES = auto()
    glIsEnablediNV = auto()
    glIsBuffer = auto()
    glIsBufferARB = auto()
    glIsFramebuffer = auto()
    glIsFramebufferEXT = auto()
    glIsProgram = auto()
    glIsProgramPipeline = auto()
    glIsProgramPipelineEXT = auto()
    glIsQuery = auto()
    glIsQueryARB = auto()
    glIsQueryEXT = auto()
    glIsRenderbuffer = auto()
    glIsRenderbufferEXT = auto()
    glIsSampler = auto()
    glIsShader = auto()
    glIsSync = auto()
    glIsTransformFeedback = auto()
    glIsVertexArray = auto()
    glIsVertexArrayOES = auto()
    glGenBuffers = auto()
    glGenBuffersARB = auto()
    glBindBuffer = auto()
    glBindBufferARB = auto()
    glDrawBuffers = auto()
    glDrawBuffersARB = auto()
    glDrawBuffersEXT = auto()
    glGenFramebuffers = auto()
    glGenFramebuffersEXT = auto()
    glBindFramebuffer = auto()
    glBindFramebufferEXT = auto()
    glFramebufferTexture = auto()
    glFramebufferTextureARB = auto()
    glFramebufferTextureOES = auto()
    glFramebufferTextureEXT = auto()
    glFramebufferTexture1D = auto()
    glFramebufferTexture1DEXT = auto()
    glFramebufferTexture2D = auto()
    glFramebufferTexture2DEXT = auto()
    glFramebufferTexture3D = auto()
    glFramebufferTexture3DEXT = auto()
    glFramebufferTexture3DOES = auto()
    glFramebufferRenderbuffer = auto()
    glFramebufferRenderbufferEXT = auto()
    glFramebufferTextureLayer = auto()
    glFramebufferTextureLayerARB = auto()
    glFramebufferTextureLayerEXT = auto()
    glFramebufferParameteri = auto()
    glDeleteFramebuffers = auto()
    glDeleteFramebuffersEXT = auto()
    glGenRenderbuffers = auto()
    glGenRenderbuffersEXT = auto()
    glRenderbufferStorage = auto()
    glRenderbufferStorageEXT = auto()
    glRenderbufferStorageMultisample = auto()
    glRenderbufferStorageMultisampleEXT = auto()
    glDeleteRenderbuffers = auto()
    glDeleteRenderbuffersEXT = auto()
    glBindRenderbuffer = auto()
    glBindRenderbufferEXT = auto()
    glFenceSync = auto()
    glClientWaitSync = auto()
    glWaitSync = auto()
    glDeleteSync = auto()
    glGenQueries = auto()
    glGenQueriesARB = auto()
    glGenQueriesEXT = auto()
    glBeginQuery = auto()
    glBeginQueryARB = auto()
    glBeginQueryEXT = auto()
    glBeginQueryIndexed = auto()
    glEndQuery = auto()
    glEndQueryARB = auto()
    glEndQueryEXT = auto()
    glEndQueryIndexed = auto()
    glBeginConditionalRender = auto()
    glEndConditionalRender = auto()
    glQueryCounter = auto()
    glQueryCounterEXT = auto()
    glDeleteQueries = auto()
    glDeleteQueriesARB = auto()
    glDeleteQueriesEXT = auto()
    glBufferData = auto()
    glBufferDataARB = auto()
    glBufferStorage = auto()
    glBufferSubData = auto()
    glBufferSubDataARB = auto()
    glCopyBufferSubData = auto()
    glBindBufferBase = auto()
    glBindBufferBaseEXT = auto()
    glBindBufferRange = auto()
    glBindBufferRangeEXT = auto()
    glBindBuffersBase = auto()
    glBindBuffersRange = auto()
    glMapBuffer = auto()
    glMapBufferARB = auto()
    glMapBufferOES = auto()
    glMapBufferRange = auto()
    glFlushMappedBufferRange = auto()
    glUnmapBuffer = auto()
    glUnmapBufferARB = auto()
    glUnmapBufferOES = auto()
    glTransformFeedbackVaryings = auto()
    glTransformFeedbackVaryingsEXT = auto()
    glGenTransformFeedbacks = auto()
    glDeleteTransformFeedbacks = auto()
    glBindTransformFeedback = auto()
    glBeginTransformFeedback = auto()
    glBeginTransformFeedbackEXT = auto()
    glPauseTransformFeedback = auto()
    glResumeTransformFeedback = auto()
    glEndTransformFeedback = auto()
    glEndTransformFeedbackEXT = auto()
    glDrawTransformFeedback = auto()
    glDrawTransformFeedbackInstanced = auto()
    glDrawTransformFeedbackStream = auto()
    glDrawTransformFeedbackStreamInstanced = auto()
    glDeleteBuffers = auto()
    glDeleteBuffersARB = auto()
    glGenVertexArrays = auto()
    glGenVertexArraysOES = auto()
    glBindVertexArray = auto()
    glBindVertexArrayOES = auto()
    glDeleteVertexArrays = auto()
    glDeleteVertexArraysOES = auto()
    glVertexAttrib1d = auto()
    glVertexAttrib1dARB = auto()
    glVertexAttrib1dv = auto()
    glVertexAttrib1dvARB = auto()
    glVertexAttrib1f = auto()
    glVertexAttrib1fARB = auto()
    glVertexAttrib1fv = auto()
    glVertexAttrib1fvARB = auto()
    glVertexAttrib1s = auto()
    glVertexAttrib1sARB = auto()
    glVertexAttrib1sv = auto()
    glVertexAttrib1svARB = auto()
    glVertexAttrib2d = auto()
    glVertexAttrib2dARB = auto()
    glVertexAttrib2dv = auto()
    glVertexAttrib2dvARB = auto()
    glVertexAttrib2f = auto()
    glVertexAttrib2fARB = auto()
    glVertexAttrib2fv = auto()
    glVertexAttrib2fvARB = auto()
    glVertexAttrib2s = auto()
    glVertexAttrib2sARB = auto()
    glVertexAttrib2sv = auto()
    glVertexAttrib2svARB = auto()
    glVertexAttrib3d = auto()
    glVertexAttrib3dARB = auto()
    glVertexAttrib3dv = auto()
    glVertexAttrib3dvARB = auto()
    glVertexAttrib3f = auto()
    glVertexAttrib3fARB = auto()
    glVertexAttrib3fv = auto()
    glVertexAttrib3fvARB = auto()
    glVertexAttrib3s = auto()
    glVertexAttrib3sARB = auto()
    glVertexAttrib3sv = auto()
    glVertexAttrib3svARB = auto()
    glVertexAttrib4Nbv = auto()
    glVertexAttrib4NbvARB = auto()
    glVertexAttrib4Niv = auto()
    glVertexAttrib4NivARB = auto()
    glVertexAttrib4Nsv = auto()
    glVertexAttrib4NsvARB = auto()
    glVertexAttrib4Nub = auto()
    glVertexAttrib4Nubv = auto()
    glVertexAttrib4NubvARB = auto()
    glVertexAttrib4Nuiv = auto()
    glVertexAttrib4NuivARB = auto()
    glVertexAttrib4Nusv = auto()
    glVertexAttrib4NusvARB = auto()
    glVertexAttrib4bv = auto()
    glVertexAttrib4bvARB = auto()
    glVertexAttrib4d = auto()
    glVertexAttrib4dARB = auto()
    glVertexAttrib4dv = auto()
    glVertexAttrib4dvARB = auto()
    glVertexAttrib4f = auto()
    glVertexAttrib4fARB = auto()
    glVertexAttrib4fv = auto()
    glVertexAttrib4fvARB = auto()
    glVertexAttrib4iv = auto()
    glVertexAttrib4ivARB = auto()
    glVertexAttrib4s = auto()
    glVertexAttrib4sARB = auto()
    glVertexAttrib4sv = auto()
    glVertexAttrib4svARB = auto()
    glVertexAttrib4ubv = auto()
    glVertexAttrib4ubvARB = auto()
    glVertexAttrib4uiv = auto()
    glVertexAttrib4uivARB = auto()
    glVertexAttrib4usv = auto()
    glVertexAttrib4usvARB = auto()
    glVertexAttribI1i = auto()
    glVertexAttribI1iEXT = auto()
    glVertexAttribI1iv = auto()
    glVertexAttribI1ivEXT = auto()
    glVertexAttribI1ui = auto()
    glVertexAttribI1uiEXT = auto()
    glVertexAttribI1uiv = auto()
    glVertexAttribI1uivEXT = auto()
    glVertexAttribI2i = auto()
    glVertexAttribI2iEXT = auto()
    glVertexAttribI2iv = auto()
    glVertexAttribI2ivEXT = auto()
    glVertexAttribI2ui = auto()
    glVertexAttribI2uiEXT = auto()
    glVertexAttribI2uiv = auto()
    glVertexAttribI2uivEXT = auto()
    glVertexAttribI3i = auto()
    glVertexAttribI3iEXT = auto()
    glVertexAttribI3iv = auto()
    glVertexAttribI3ivEXT = auto()
    glVertexAttribI3ui = auto()
    glVertexAttribI3uiEXT = auto()
    glVertexAttribI3uiv = auto()
    glVertexAttribI3uivEXT = auto()
    glVertexAttribI4bv = auto()
    glVertexAttribI4bvEXT = auto()
    glVertexAttribI4i = auto()
    glVertexAttribI4iEXT = auto()
    glVertexAttribI4iv = auto()
    glVertexAttribI4ivEXT = auto()
    glVertexAttribI4sv = auto()
    glVertexAttribI4svEXT = auto()
    glVertexAttribI4ubv = auto()
    glVertexAttribI4ubvEXT = auto()
    glVertexAttribI4ui = auto()
    glVertexAttribI4uiEXT = auto()
    glVertexAttribI4uiv = auto()
    glVertexAttribI4uivEXT = auto()
    glVertexAttribI4usv = auto()
    glVertexAttribI4usvEXT = auto()
    glVertexAttribL1d = auto()
    glVertexAttribL1dEXT = auto()
    glVertexAttribL1dv = auto()
    glVertexAttribL1dvEXT = auto()
    glVertexAttribL2d = auto()
    glVertexAttribL2dEXT = auto()
    glVertexAttribL2dv = auto()
    glVertexAttribL2dvEXT = auto()
    glVertexAttribL3d = auto()
    glVertexAttribL3dEXT = auto()
    glVertexAttribL3dv = auto()
    glVertexAttribL3dvEXT = auto()
    glVertexAttribL4d = auto()
    glVertexAttribL4dEXT = auto()
    glVertexAttribL4dv = auto()
    glVertexAttribL4dvEXT = auto()
    glVertexAttribP1ui = auto()
    glVertexAttribP1uiv = auto()
    glVertexAttribP2ui = auto()
    glVertexAttribP2uiv = auto()
    glVertexAttribP3ui = auto()
    glVertexAttribP3uiv = auto()
    glVertexAttribP4ui = auto()
    glVertexAttribP4uiv = auto()
    glVertexAttribPointer = auto()
    glVertexAttribPointerARB = auto()
    glVertexAttribIPointer = auto()
    glVertexAttribIPointerEXT = auto()
    glVertexAttribLPointer = auto()
    glVertexAttribLPointerEXT = auto()
    glVertexAttribBinding = auto()
    glVertexAttribFormat = auto()
    glVertexAttribIFormat = auto()
    glVertexAttribLFormat = auto()
    glVertexAttribDivisor = auto()
    glVertexAttribDivisorARB = auto()
    glBindAttribLocation = auto()
    glBindFragDataLocation = auto()
    glBindFragDataLocationEXT = auto()
    glBindFragDataLocationIndexed = auto()
    glEnableVertexAttribArray = auto()
    glEnableVertexAttribArrayARB = auto()
    glDisableVertexAttribArray = auto()
    glDisableVertexAttribArrayARB = auto()
    glBindVertexBuffer = auto()
    glBindVertexBuffers = auto()
    glVertexBindingDivisor = auto()
    glBindImageTexture = auto()
    glBindImageTextureEXT = auto()
    glBindImageTextures = auto()
    glGenSamplers = auto()
    glBindSampler = auto()
    glBindSamplers = auto()
    glBindTextures = auto()
    glDeleteSamplers = auto()
    glSamplerParameteri = auto()
    glSamplerParameterf = auto()
    glSamplerParameteriv = auto()
    glSamplerParameterfv = auto()
    glSamplerParameterIiv = auto()
    glSamplerParameterIivEXT = auto()
    glSamplerParameterIivOES = auto()
    glSamplerParameterIuiv = auto()
    glSamplerParameterIuivEXT = auto()
    glSamplerParameterIuivOES = auto()
    glPatchParameteri = auto()
    glPatchParameteriEXT = auto()
    glPatchParameteriOES = auto()
    glPatchParameterfv = auto()
    glPointParameterf = auto()
    glPointParameterfARB = auto()
    glPointParameterfEXT = auto()
    glPointParameterfv = auto()
    glPointParameterfvARB = auto()
    glPointParameterfvEXT = auto()
    glPointParameteri = auto()
    glPointParameteriv = auto()
    glDispatchCompute = auto()
    glDispatchComputeIndirect = auto()
    glMemoryBarrier = auto()
    glMemoryBarrierEXT = auto()
    glMemoryBarrierByRegion = auto()
    glTextureBarrier = auto()
    glClearDepthf = auto()
    glClearBufferfv = auto()
    glClearBufferiv = auto()
    glClearBufferuiv = auto()
    glClearBufferfi = auto()
    glClearBufferData = auto()
    glClearBufferSubData = auto()
    glClearTexImage = auto()
    glClearTexSubImage = auto()
    glInvalidateBufferData = auto()
    glInvalidateBufferSubData = auto()
    glInvalidateFramebuffer = auto()
    glInvalidateSubFramebuffer = auto()
    glInvalidateTexImage = auto()
    glInvalidateTexSubImage = auto()
    glScissorArrayv = auto()
    glScissorArrayvOES = auto()
    glScissorArrayvNV = auto()
    glScissorIndexed = auto()
    glScissorIndexedOES = auto()
    glScissorIndexedNV = auto()
    glScissorIndexedv = auto()
    glScissorIndexedvOES = auto()
    glScissorIndexedvNV = auto()
    glViewportIndexedf = auto()
    glViewportIndexedfOES = auto()
    glViewportIndexedfNV = auto()
    glViewportIndexedfv = auto()
    glViewportIndexedfvOES = auto()
    glViewportIndexedfvNV = auto()
    glViewportArrayv = auto()
    glViewportArrayvOES = auto()
    glViewportArrayvNV = auto()
    glUniformBlockBinding = auto()
    glShaderStorageBlockBinding = auto()
    glUniformSubroutinesuiv = auto()
    glUniform1f = auto()
    glUniform1i = auto()
    glUniform1ui = auto()
    glUniform1uiEXT = auto()
    glUniform1d = auto()
    glUniform2f = auto()
    glUniform2i = auto()
    glUniform2ui = auto()
    glUniform2uiEXT = auto()
    glUniform2d = auto()
    glUniform3f = auto()
    glUniform3i = auto()
    glUniform3ui = auto()
    glUniform3uiEXT = auto()
    glUniform3d = auto()
    glUniform4f = auto()
    glUniform4i = auto()
    glUniform4ui = auto()
    glUniform4uiEXT = auto()
    glUniform4d = auto()
    glUniform1fv = auto()
    glUniform1iv = auto()
    glUniform1uiv = auto()
    glUniform1uivEXT = auto()
    glUniform1dv = auto()
    glUniform2fv = auto()
    glUniform2iv = auto()
    glUniform2uiv = auto()
    glUniform2uivEXT = auto()
    glUniform2dv = auto()
    glUniform3fv = auto()
    glUniform3iv = auto()
    glUniform3uiv = auto()
    glUniform3uivEXT = auto()
    glUniform3dv = auto()
    glUniform4fv = auto()
    glUniform4iv = auto()
    glUniform4uiv = auto()
    glUniform4uivEXT = auto()
    glUniform4dv = auto()
    glUniformMatrix2fv = auto()
    glUniformMatrix2x3fv = auto()
    glUniformMatrix2x4fv = auto()
    glUniformMatrix3fv = auto()
    glUniformMatrix3x2fv = auto()
    glUniformMatrix3x4fv = auto()
    glUniformMatrix4fv = auto()
    glUniformMatrix4x2fv = auto()
    glUniformMatrix4x3fv = auto()
    glUniformMatrix2dv = auto()
    glUniformMatrix2x3dv = auto()
    glUniformMatrix2x4dv = auto()
    glUniformMatrix3dv = auto()
    glUniformMatrix3x2dv = auto()
    glUniformMatrix3x4dv = auto()
    glUniformMatrix4dv = auto()
    glUniformMatrix4x2dv = auto()
    glUniformMatrix4x3dv = auto()
    glProgramUniform1f = auto()
    glProgramUniform1fEXT = auto()
    glProgramUniform1i = auto()
    glProgramUniform1iEXT = auto()
    glProgramUniform1ui = auto()
    glProgramUniform1uiEXT = auto()
    glProgramUniform1d = auto()
    glProgramUniform1dEXT = auto()
    glProgramUniform2f = auto()
    glProgramUniform2fEXT = auto()
    glProgramUniform2i = auto()
    glProgramUniform2iEXT = auto()
    glProgramUniform2ui = auto()
    glProgramUniform2uiEXT = auto()
    glProgramUniform2d = auto()
    glProgramUniform2dEXT = auto()
    glProgramUniform3f = auto()
    glProgramUniform3fEXT = auto()
    glProgramUniform3i = auto()
    glProgramUniform3iEXT = auto()
    glProgramUniform3ui = auto()
    glProgramUniform3uiEXT = auto()
    glProgramUniform3d = auto()
    glProgramUniform3dEXT = auto()
    glProgramUniform4f = auto()
    glProgramUniform4fEXT = auto()
    glProgramUniform4i = auto()
    glProgramUniform4iEXT = auto()
    glProgramUniform4ui = auto()
    glProgramUniform4uiEXT = auto()
    glProgramUniform4d = auto()
    glProgramUniform4dEXT = auto()
    glProgramUniform1fv = auto()
    glProgramUniform1fvEXT = auto()
    glProgramUniform1iv = auto()
    glProgramUniform1ivEXT = auto()
    glProgramUniform1uiv = auto()
    glProgramUniform1uivEXT = auto()
    glProgramUniform1dv = auto()
    glProgramUniform1dvEXT = auto()
    glProgramUniform2fv = auto()
    glProgramUniform2fvEXT = auto()
    glProgramUniform2iv = auto()
    glProgramUniform2ivEXT = auto()
    glProgramUniform2uiv = auto()
    glProgramUniform2uivEXT = auto()
    glProgramUniform2dv = auto()
    glProgramUniform2dvEXT = auto()
    glProgramUniform3fv = auto()
    glProgramUniform3fvEXT = auto()
    glProgramUniform3iv = auto()
    glProgramUniform3ivEXT = auto()
    glProgramUniform3uiv = auto()
    glProgramUniform3uivEXT = auto()
    glProgramUniform3dv = auto()
    glProgramUniform3dvEXT = auto()
    glProgramUniform4fv = auto()
    glProgramUniform4fvEXT = auto()
    glProgramUniform4iv = auto()
    glProgramUniform4ivEXT = auto()
    glProgramUniform4uiv = auto()
    glProgramUniform4uivEXT = auto()
    glProgramUniform4dv = auto()
    glProgramUniform4dvEXT = auto()
    glProgramUniformMatrix2fv = auto()
    glProgramUniformMatrix2fvEXT = auto()
    glProgramUniformMatrix2x3fv = auto()
    glProgramUniformMatrix2x3fvEXT = auto()
    glProgramUniformMatrix2x4fv = auto()
    glProgramUniformMatrix2x4fvEXT = auto()
    glProgramUniformMatrix3fv = auto()
    glProgramUniformMatrix3fvEXT = auto()
    glProgramUniformMatrix3x2fv = auto()
    glProgramUniformMatrix3x2fvEXT = auto()
    glProgramUniformMatrix3x4fv = auto()
    glProgramUniformMatrix3x4fvEXT = auto()
    glProgramUniformMatrix4fv = auto()
    glProgramUniformMatrix4fvEXT = auto()
    glProgramUniformMatrix4x2fv = auto()
    glProgramUniformMatrix4x2fvEXT = auto()
    glProgramUniformMatrix4x3fv = auto()
    glProgramUniformMatrix4x3fvEXT = auto()
    glProgramUniformMatrix2dv = auto()
    glProgramUniformMatrix2dvEXT = auto()
    glProgramUniformMatrix2x3dv = auto()
    glProgramUniformMatrix2x3dvEXT = auto()
    glProgramUniformMatrix2x4dv = auto()
    glProgramUniformMatrix2x4dvEXT = auto()
    glProgramUniformMatrix3dv = auto()
    glProgramUniformMatrix3dvEXT = auto()
    glProgramUniformMatrix3x2dv = auto()
    glProgramUniformMatrix3x2dvEXT = auto()
    glProgramUniformMatrix3x4dv = auto()
    glProgramUniformMatrix3x4dvEXT = auto()
    glProgramUniformMatrix4dv = auto()
    glProgramUniformMatrix4dvEXT = auto()
    glProgramUniformMatrix4x2dv = auto()
    glProgramUniformMatrix4x2dvEXT = auto()
    glProgramUniformMatrix4x3dv = auto()
    glProgramUniformMatrix4x3dvEXT = auto()
    glDrawRangeElements = auto()
    glDrawRangeElementsEXT = auto()
    glDrawRangeElementsBaseVertex = auto()
    glDrawRangeElementsBaseVertexEXT = auto()
    glDrawRangeElementsBaseVertexOES = auto()
    glDrawArraysInstancedBaseInstance = auto()
    glDrawArraysInstancedBaseInstanceEXT = auto()
    glDrawArraysInstanced = auto()
    glDrawArraysInstancedARB = auto()
    glDrawArraysInstancedEXT = auto()
    glDrawElementsInstanced = auto()
    glDrawElementsInstancedARB = auto()
    glDrawElementsInstancedEXT = auto()
    glDrawElementsInstancedBaseInstance = auto()
    glDrawElementsInstancedBaseInstanceEXT = auto()
    glDrawElementsBaseVertex = auto()
    glDrawElementsBaseVertexEXT = auto()
    glDrawElementsBaseVertexOES = auto()
    glDrawElementsInstancedBaseVertex = auto()
    glDrawElementsInstancedBaseVertexEXT = auto()
    glDrawElementsInstancedBaseVertexOES = auto()
    glDrawElementsInstancedBaseVertexBaseInstance = auto()
    glDrawElementsInstancedBaseVertexBaseInstanceEXT = auto()
    glMultiDrawArrays = auto()
    glMultiDrawArraysEXT = auto()
    glMultiDrawElements = auto()
    glMultiDrawElementsBaseVertex = auto()
    glMultiDrawElementsBaseVertexEXT = auto()
    glMultiDrawElementsBaseVertexOES = auto()
    glMultiDrawArraysIndirect = auto()
    glMultiDrawElementsIndirect = auto()
    glDrawArraysIndirect = auto()
    glDrawElementsIndirect = auto()
    glBlitFramebuffer = auto()
    glBlitFramebufferEXT = auto()
    glPrimitiveBoundingBox = auto()
    glPrimitiveBoundingBoxEXT = auto()
    glPrimitiveBoundingBoxOES = auto()
    glBlendBarrier = auto()
    glFramebufferTexture2DMultisampleEXT = auto()
    glDiscardFramebufferEXT = auto()
    glDepthRangeArrayfvOES = auto()
    glDepthRangeArrayfvNV = auto()
    glDepthRangeIndexedfOES = auto()
    glDepthRangeIndexedfNV = auto()
    glNamedStringARB = auto()
    glDeleteNamedStringARB = auto()
    glCompileShaderIncludeARB = auto()
    glIsNamedStringARB = auto()
    glGetNamedStringARB = auto()
    glGetNamedStringivARB = auto()
    glDispatchComputeGroupSizeARB = auto()
    glMultiDrawArraysIndirectCountARB = auto()
    glMultiDrawElementsIndirectCountARB = auto()
    glRasterSamplesEXT = auto()
    glDepthBoundsEXT = auto()
    glPolygonOffsetClampEXT = auto()
    glInsertEventMarkerEXT = auto()
    glPushGroupMarkerEXT = auto()
    glPopGroupMarkerEXT = auto()
    glFrameTerminatorGREMEDY = auto()
    glStringMarkerGREMEDY = auto()
    glFramebufferTextureMultiviewOVR = auto()
    glFramebufferTextureMultisampleMultiviewOVR = auto()
    glCompressedTextureImage1DEXT = auto()
    glCompressedTextureImage2DEXT = auto()
    glCompressedTextureImage3DEXT = auto()
    glCompressedTextureSubImage1DEXT = auto()
    glCompressedTextureSubImage2DEXT = auto()
    glCompressedTextureSubImage3DEXT = auto()
    glGenerateTextureMipmapEXT = auto()
    glGetPointeri_vEXT = auto()
    glGetDoubleIndexedvEXT = auto()
    glGetPointerIndexedvEXT = auto()
    glGetIntegerIndexedvEXT = auto()
    glGetBooleanIndexedvEXT = auto()
    glGetFloatIndexedvEXT = auto()
    glGetMultiTexImageEXT = auto()
    glGetMultiTexParameterfvEXT = auto()
    glGetMultiTexParameterivEXT = auto()
    glGetMultiTexParameterIivEXT = auto()
    glGetMultiTexParameterIuivEXT = auto()
    glGetMultiTexLevelParameterfvEXT = auto()
    glGetMultiTexLevelParameterivEXT = auto()
    glGetCompressedMultiTexImageEXT = auto()
    glGetNamedBufferPointervEXT = auto()
    glGetNamedBufferPointerv = auto()
    glGetNamedProgramivEXT = auto()
    glGetNamedFramebufferAttachmentParameterivEXT = auto()
    glGetNamedFramebufferAttachmentParameteriv = auto()
    glGetNamedBufferParameterivEXT = auto()
    glGetNamedBufferParameteriv = auto()
    glCheckNamedFramebufferStatusEXT = auto()
    glCheckNamedFramebufferStatus = auto()
    glGetNamedBufferSubDataEXT = auto()
    glGetNamedFramebufferParameterivEXT = auto()
    glGetFramebufferParameterivEXT = auto()
    glGetNamedFramebufferParameteriv = auto()
    glGetNamedRenderbufferParameterivEXT = auto()
    glGetNamedRenderbufferParameteriv = auto()
    glGetVertexArrayIntegervEXT = auto()
    glGetVertexArrayPointervEXT = auto()
    glGetVertexArrayIntegeri_vEXT = auto()
    glGetVertexArrayPointeri_vEXT = auto()
    glGetCompressedTextureImageEXT = auto()
    glGetTextureImageEXT = auto()
    glGetTextureParameterivEXT = auto()
    glGetTextureParameterfvEXT = auto()
    glGetTextureParameterIivEXT = auto()
    glGetTextureParameterIuivEXT = auto()
    glGetTextureLevelParameterivEXT = auto()
    glGetTextureLevelParameterfvEXT = auto()
    glBindMultiTextureEXT = auto()
    glMapNamedBufferEXT = auto()
    glMapNamedBuffer = auto()
    glMapNamedBufferRangeEXT = auto()
    glFlushMappedNamedBufferRangeEXT = auto()
    glUnmapNamedBufferEXT = auto()
    glUnmapNamedBuffer = auto()
    glClearNamedBufferDataEXT = auto()
    glClearNamedBufferData = auto()
    glClearNamedBufferSubDataEXT = auto()
    glNamedBufferDataEXT = auto()
    glNamedBufferStorageEXT = auto()
    glNamedBufferSubDataEXT = auto()
    glNamedCopyBufferSubDataEXT = auto()
    glNamedFramebufferTextureEXT = auto()
    glNamedFramebufferTexture = auto()
    glNamedFramebufferTexture1DEXT = auto()
    glNamedFramebufferTexture2DEXT = auto()
    glNamedFramebufferTexture3DEXT = auto()
    glNamedFramebufferRenderbufferEXT = auto()
    glNamedFramebufferRenderbuffer = auto()
    glNamedFramebufferTextureLayerEXT = auto()
    glNamedFramebufferTextureLayer = auto()
    glNamedFramebufferParameteriEXT = auto()
    glNamedFramebufferParameteri = auto()
    glNamedRenderbufferStorageEXT = auto()
    glNamedRenderbufferStorage = auto()
    glNamedRenderbufferStorageMultisampleEXT = auto()
    glNamedRenderbufferStorageMultisample = auto()
    glFramebufferDrawBufferEXT = auto()
    glNamedFramebufferDrawBuffer = auto()
    glFramebufferDrawBuffersEXT = auto()
    glNamedFramebufferDrawBuffers = auto()
    glFramebufferReadBufferEXT = auto()
    glNamedFramebufferReadBuffer = auto()
    glTextureBufferEXT = auto()
    glTextureBufferRangeEXT = auto()
    glTextureImage1DEXT = auto()
    glTextureImage2DEXT = auto()
    glTextureImage3DEXT = auto()
    glTextureParameterfEXT = auto()
    glTextureParameterfvEXT = auto()
    glTextureParameteriEXT = auto()
    glTextureParameterivEXT = auto()
    glTextureParameterIivEXT = auto()
    glTextureParameterIuivEXT = auto()
    glTextureStorage1DEXT = auto()
    glTextureStorage2DEXT = auto()
    glTextureStorage3DEXT = auto()
    glTextureStorage2DMultisampleEXT = auto()
    glTextureStorage3DMultisampleEXT = auto()
    glTextureSubImage1DEXT = auto()
    glTextureSubImage2DEXT = auto()
    glTextureSubImage3DEXT = auto()
    glCopyTextureImage1DEXT = auto()
    glCopyTextureImage2DEXT = auto()
    glCopyTextureSubImage1DEXT = auto()
    glCopyTextureSubImage2DEXT = auto()
    glCopyTextureSubImage3DEXT = auto()
    glMultiTexParameteriEXT = auto()
    glMultiTexParameterivEXT = auto()
    glMultiTexParameterfEXT = auto()
    glMultiTexParameterfvEXT = auto()
    glMultiTexImage1DEXT = auto()
    glMultiTexImage2DEXT = auto()
    glMultiTexSubImage1DEXT = auto()
    glMultiTexSubImage2DEXT = auto()
    glCopyMultiTexImage1DEXT = auto()
    glCopyMultiTexImage2DEXT = auto()
    glCopyMultiTexSubImage1DEXT = auto()
    glCopyMultiTexSubImage2DEXT = auto()
    glMultiTexImage3DEXT = auto()
    glMultiTexSubImage3DEXT = auto()
    glCopyMultiTexSubImage3DEXT = auto()
    glCompressedMultiTexImage3DEXT = auto()
    glCompressedMultiTexImage2DEXT = auto()
    glCompressedMultiTexImage1DEXT = auto()
    glCompressedMultiTexSubImage3DEXT = auto()
    glCompressedMultiTexSubImage2DEXT = auto()
    glCompressedMultiTexSubImage1DEXT = auto()
    glMultiTexBufferEXT = auto()
    glMultiTexParameterIivEXT = auto()
    glMultiTexParameterIuivEXT = auto()
    glGenerateMultiTexMipmapEXT = auto()
    glVertexArrayVertexAttribOffsetEXT = auto()
    glVertexArrayVertexAttribIOffsetEXT = auto()
    glEnableVertexArrayAttribEXT = auto()
    glEnableVertexArrayAttrib = auto()
    glDisableVertexArrayAttribEXT = auto()
    glDisableVertexArrayAttrib = auto()
    glVertexArrayBindVertexBufferEXT = auto()
    glVertexArrayVertexBuffer = auto()
    glVertexArrayVertexAttribFormatEXT = auto()
    glVertexArrayAttribFormat = auto()
    glVertexArrayVertexAttribIFormatEXT = auto()
    glVertexArrayAttribIFormat = auto()
    glVertexArrayVertexAttribLFormatEXT = auto()
    glVertexArrayAttribLFormat = auto()
    glVertexArrayVertexAttribBindingEXT = auto()
    glVertexArrayAttribBinding = auto()
    glVertexArrayVertexBindingDivisorEXT = auto()
    glVertexArrayBindingDivisor = auto()
    glVertexArrayVertexAttribLOffsetEXT = auto()
    glVertexArrayVertexAttribDivisorEXT = auto()
    glCreateTransformFeedbacks = auto()
    glTransformFeedbackBufferBase = auto()
    glTransformFeedbackBufferRange = auto()
    glGetTransformFeedbacki64_v = auto()
    glGetTransformFeedbacki_v = auto()
    glGetTransformFeedbackiv = auto()
    glCreateBuffers = auto()
    glGetNamedBufferSubData = auto()
    glNamedBufferStorage = auto()
    glNamedBufferData = auto()
    glNamedBufferSubData = auto()
    glCopyNamedBufferSubData = auto()
    glClearNamedBufferSubData = auto()
    glMapNamedBufferRange = auto()
    glFlushMappedNamedBufferRange = auto()
    glGetNamedBufferParameteri64v = auto()
    glCreateFramebuffers = auto()
    glInvalidateNamedFramebufferData = auto()
    glInvalidateNamedFramebufferSubData = auto()
    glClearNamedFramebufferiv = auto()
    glClearNamedFramebufferuiv = auto()
    glClearNamedFramebufferfv = auto()
    glClearNamedFramebufferfi = auto()
    glBlitNamedFramebuffer = auto()
    glCreateRenderbuffers = auto()
    glCreateTextures = auto()
    glTextureBuffer = auto()
    glTextureBufferRange = auto()
    glTextureStorage1D = auto()
    glTextureStorage2D = auto()
    glTextureStorage3D = auto()
    glTextureStorage2DMultisample = auto()
    glTextureStorage3DMultisample = auto()
    glTextureSubImage1D = auto()
    glTextureSubImage2D = auto()
    glTextureSubImage3D = auto()
    glCompressedTextureSubImage1D = auto()
    glCompressedTextureSubImage2D = auto()
    glCompressedTextureSubImage3D = auto()
    glCopyTextureSubImage1D = auto()
    glCopyTextureSubImage2D = auto()
    glCopyTextureSubImage3D = auto()
    glTextureParameterf = auto()
    glTextureParameterfv = auto()
    glTextureParameteri = auto()
    glTextureParameterIiv = auto()
    glTextureParameterIuiv = auto()
    glTextureParameteriv = auto()
    glGenerateTextureMipmap = auto()
    glBindTextureUnit = auto()
    glGetTextureImage = auto()
    glGetTextureSubImage = auto()
    glGetCompressedTextureImage = auto()
    glGetCompressedTextureSubImage = auto()
    glGetTextureLevelParameterfv = auto()
    glGetTextureLevelParameteriv = auto()
    glGetTextureParameterIiv = auto()
    glGetTextureParameterIuiv = auto()
    glGetTextureParameterfv = auto()
    glGetTextureParameteriv = auto()
    glCreateVertexArrays = auto()
    glCreateSamplers = auto()
    glCreateProgramPipelines = auto()
    glCreateQueries = auto()
    glVertexArrayElementBuffer = auto()
    glVertexArrayVertexBuffers = auto()
    glGetVertexArrayiv = auto()
    glGetVertexArrayIndexed64iv = auto()
    glGetVertexArrayIndexediv = auto()
    glGetQueryBufferObjecti64v = auto()
    glGetQueryBufferObjectiv = auto()
    glGetQueryBufferObjectui64v = auto()
    glGetQueryBufferObjectuiv = auto()
    wglDXSetResourceShareHandleNV = auto()
    wglDXOpenDeviceNV = auto()
    wglDXCloseDeviceNV = auto()
    wglDXRegisterObjectNV = auto()
    wglDXUnregisterObjectNV = auto()
    wglDXObjectAccessNV = auto()
    wglDXLockObjectsNV = auto()
    wglDXUnlockObjectsNV = auto()

    glIndirectSubCommand = auto()

    glContextInit = auto()

    glMultiDrawArraysIndirectCount = auto()
    glMultiDrawElementsIndirectCount = auto()
    glPolygonOffsetClamp = auto()
    glMaxShaderCompilerThreadsARB = auto()
    glMaxShaderCompilerThreadsKHR = auto()

    glSpecializeShader = auto()
    glSpecializeShaderARB = auto()

    glUniform1fARB = auto()
    glUniform1iARB = auto()
    glUniform2fARB = auto()
    glUniform2iARB = auto()
    glUniform3fARB = auto()
    glUniform3iARB = auto()
    glUniform4fARB = auto()
    glUniform4iARB = auto()
    glUniform1fvARB = auto()
    glUniform1ivARB = auto()
    glUniform2fvARB = auto()
    glUniform2ivARB = auto()
    glUniform3fvARB = auto()
    glUniform3ivARB = auto()
    glUniform4fvARB = auto()
    glUniform4ivARB = auto()
    glUniformMatrix2fvARB = auto()
    glUniformMatrix3fvARB = auto()
    glUniformMatrix4fvARB = auto()

    glGetUnsignedBytevEXT = auto()
    glGetUnsignedBytei_vEXT = auto()
    glDeleteMemoryObjectsEXT = auto()
    glIsMemoryObjectEXT = auto()
    glCreateMemoryObjectsEXT = auto()
    glMemoryObjectParameterivEXT = auto()
    glGetMemoryObjectParameterivEXT = auto()
    glTexStorageMem2DEXT = auto()
    glTexStorageMem2DMultisampleEXT = auto()
    glTexStorageMem3DEXT = auto()
    glTexStorageMem3DMultisampleEXT = auto()
    glBufferStorageMemEXT = auto()
    glTextureStorageMem2DEXT = auto()
    glTextureStorageMem2DMultisampleEXT = auto()
    glTextureStorageMem3DEXT = auto()
    glTextureStorageMem3DMultisampleEXT = auto()
    glNamedBufferStorageMemEXT = auto()
    glTexStorageMem1DEXT = auto()
    glTextureStorageMem1DEXT = auto()
    glGenSemaphoresEXT = auto()
    glDeleteSemaphoresEXT = auto()
    glIsSemaphoreEXT = auto()
    glSemaphoreParameterui64vEXT = auto()
    glGetSemaphoreParameterui64vEXT = auto()
    glWaitSemaphoreEXT = auto()
    glSignalSemaphoreEXT = auto()
    glImportMemoryFdEXT = auto()
    glImportSemaphoreFdEXT = auto()
    glImportMemoryWin32HandleEXT = auto()
    glImportMemoryWin32NameEXT = auto()
    glImportSemaphoreWin32HandleEXT = auto()
    glImportSemaphoreWin32NameEXT = auto()
    glAcquireKeyedMutexWin32EXT = auto()
    glReleaseKeyedMutexWin32EXT = auto()

    ContextConfiguration = auto()

    glTextureFoveationParametersQCOM = auto()

    glBufferStorageEXT = auto()

    CoherentMapWrite = auto()

    glBeginPerfQueryINTEL = auto()
    glCreatePerfQueryINTEL = auto()
    glDeletePerfQueryINTEL = auto()
    glEndPerfQueryINTEL = auto()
    glGetFirstPerfQueryIdINTEL = auto()
    glGetNextPerfQueryIdINTEL = auto()
    glGetPerfCounterInfoINTEL = auto()
    glGetPerfQueryDataINTEL = auto()
    glGetPerfQueryIdByNameINTEL = auto()
    glGetPerfQueryInfoINTEL = auto()

    glBlendEquationARB = auto()
    glPrimitiveBoundingBoxARB = auto()

    SwapBuffers = auto()
    wglSwapBuffers = auto()
    glXSwapBuffers = auto()
    CGLFlushDrawable = auto()
    eglSwapBuffers = auto()
    eglPostSubBufferNV = auto()
    eglSwapBuffersWithDamageEXT = auto()
    eglSwapBuffersWithDamageKHR = auto()

    ImplicitThreadSwitch = auto()

    Count = auto()


class D3D11Chunk(Enum):
    Dummy = 0

    # C:\svn_pool\renderdoc\renderdoc\core\core.h
    DriverInit = 1
    InitialContentsList = auto()
    InitialContents = auto()
    CaptureBegin = auto()
    CaptureScope = auto()
    CaptureEnd = auto()

    FirstDriverChunk = 1000

    SetResourceName = auto()
    CreateSwapBuffer = auto()
    CreateTexture1D = auto()
    CreateTexture2D = auto()
    CreateTexture3D = auto()
    CreateBuffer = auto()
    CreateVertexShader = auto()
    CreateHullShader = auto()
    CreateDomainShader = auto()
    CreateGeometryShader = auto()
    CreateGeometryShaderWithStreamOutput = auto()
    CreatePixelShader = auto()
    CreateComputeShader = auto()
    GetClassInstance = auto()
    CreateClassInstance = auto()
    CreateClassLinkage = auto()
    CreateShaderResourceView = auto()
    CreateRenderTargetView = auto()
    CreateDepthStencilView = auto()
    CreateUnorderedAccessView = auto()
    CreateInputLayout = auto()
    CreateBlendState = auto()
    CreateDepthStencilState = auto()
    CreateRasterizerState = auto()
    CreateSamplerState = auto()
    CreateQuery = auto()
    CreatePredicate = auto()
    CreateCounter = auto()
    CreateDeferredContext = auto()
    SetExceptionMode = auto()
    OpenSharedResource = auto()
    IASetInputLayout = auto()
    IASetVertexBuffers = auto()
    IASetIndexBuffer = auto()
    IASetPrimitiveTopology = auto()
    VSSetConstantBuffers = auto()
    VSSetShaderResources = auto()
    VSSetSamplers = auto()
    VSSetShader = auto()
    HSSetConstantBuffers = auto()
    HSSetShaderResources = auto()
    HSSetSamplers = auto()
    HSSetShader = auto()
    DSSetConstantBuffers = auto()
    DSSetShaderResources = auto()
    DSSetSamplers = auto()
    DSSetShader = auto()
    GSSetConstantBuffers = auto()
    GSSetShaderResources = auto()
    GSSetSamplers = auto()
    GSSetShader = auto()
    SOSetTargets = auto()
    PSSetConstantBuffers = auto()
    PSSetShaderResources = auto()
    PSSetSamplers = auto()
    PSSetShader = auto()
    CSSetConstantBuffers = auto()
    CSSetShaderResources = auto()
    CSSetUnorderedAccessViews = auto()
    CSSetSamplers = auto()
    CSSetShader = auto()
    RSSetViewports = auto()
    RSSetScissorRects = auto()
    RSSetState = auto()
    OMSetRenderTargets = auto()
    OMSetRenderTargetsAndUnorderedAccessViews = auto()
    OMSetBlendState = auto()
    OMSetDepthStencilState = auto()
    DrawIndexedInstanced = auto()
    DrawInstanced = auto()
    DrawIndexed = auto()
    Draw = auto()
    DrawAuto = auto()
    DrawIndexedInstancedIndirect = auto()
    DrawInstancedIndirect = auto()
    Map = auto()
    Unmap = auto()
    CopySubresourceRegion = auto()
    CopyResource = auto()
    UpdateSubresource = auto()
    CopyStructureCount = auto()
    ResolveSubresource = auto()
    GenerateMips = auto()
    ClearDepthStencilView = auto()
    ClearRenderTargetView = auto()
    ClearUnorderedAccessViewUint = auto()
    ClearUnorderedAccessViewFloat = auto()
    ClearState = auto()
    ExecuteCommandList = auto()
    Dispatch = auto()
    DispatchIndirect = auto()
    FinishCommandList = auto()
    Flush = auto()
    SetPredication = auto()
    SetResourceMinLOD = auto()
    Begin = auto()
    End = auto()
    CreateRasterizerState1 = auto()
    CreateBlendState1 = auto()
    CopySubresourceRegion1 = auto()
    UpdateSubresource1 = auto()
    ClearView = auto()
    VSSetConstantBuffers1 = auto()
    HSSetConstantBuffers1 = auto()
    DSSetConstantBuffers1 = auto()
    GSSetConstantBuffers1 = auto()
    PSSetConstantBuffers1 = auto()
    CSSetConstantBuffers1 = auto()
    PushMarker = auto()
    SetMarker = auto()
    PopMarker = auto()
    SetShaderDebugPath = auto()
    DiscardResource = auto()
    DiscardView = auto()
    DiscardView1 = auto()
    CreateRasterizerState2 = auto()
    CreateQuery1 = auto()
    CreateTexture2D1 = auto()
    CreateTexture3D1 = auto()
    CreateShaderResourceView1 = auto()
    CreateRenderTargetView1 = auto()
    CreateUnorderedAccessView1 = auto()
    SwapchainPresent = auto()
    PostExecuteCommandList = auto()
    PostFinishCommandListSet = auto()
    SwapDeviceContextState = auto()
    ExternalDXGIResource = auto()
    OpenSharedResource1 = auto()
    OpenSharedResourceByName = auto()
    
    Count = auto()

class VulkanChunk(Enum):
    Dummy = 0

    # C:\svn_pool\renderdoc\renderdoc\core\core.h
    DriverInit = 1
    InitialContentsList = auto()
    InitialContents = auto()
    CaptureBegin = auto()
    CaptureScope = auto()
    CaptureEnd = auto()

    FirstDriverChunk = 1000

    vkCreateDevice = auto()
    vkGetDeviceQueue = auto()
    vkAllocateMemory = auto()
    vkUnmapMemory = auto()
    vkFlushMappedMemoryRanges = auto()
    vkCreateCommandPool = auto()
    vkResetCommandPool = auto()
    vkAllocateCommandBuffers = auto()
    vkCreateFramebuffer = auto()
    vkCreateRenderPass = auto()
    vkCreateDescriptorPool = auto()
    vkCreateDescriptorSetLayout = auto()
    vkCreateBuffer = auto()
    vkCreateBufferView = auto()
    vkCreateImage = auto()
    vkCreateImageView = auto()
    vkCreateDepthTargetView = auto()
    vkCreateSampler = auto()
    vkCreateShaderModule = auto()
    vkCreatePipelineLayout = auto()
    vkCreatePipelineCache = auto()
    vkCreateGraphicsPipelines = auto()
    vkCreateComputePipelines = auto()
    vkGetSwapchainImagesKHR = auto()
    vkCreateSemaphore = auto()
    vkCreateFence = auto()
    vkGetFenceStatus = auto()
    vkResetFences = auto()
    vkWaitForFences = auto()
    vkCreateEvent = auto()
    vkGetEventStatus = auto()
    vkSetEvent = auto()
    vkResetEvent = auto()
    vkCreateQueryPool = auto()
    vkAllocateDescriptorSets = auto()
    vkUpdateDescriptorSets = auto()
    vkBeginCommandBuffer = auto()
    vkEndCommandBuffer = auto()
    vkQueueWaitIdle = auto()
    vkDeviceWaitIdle = auto()
    vkQueueSubmit = auto()
    vkBindBufferMemory = auto()
    vkBindImageMemory = auto()
    vkQueueBindSparse = auto()
    vkCmdBeginRenderPass = auto()
    vkCmdNextSubpass = auto()
    vkCmdExecuteCommands = auto()
    vkCmdEndRenderPass = auto()
    vkCmdBindPipeline = auto()
    vkCmdSetViewport = auto()
    vkCmdSetScissor = auto()
    vkCmdSetLineWidth = auto()
    vkCmdSetDepthBias = auto()
    vkCmdSetBlendConstants = auto()
    vkCmdSetDepthBounds = auto()
    vkCmdSetStencilCompareMask = auto()
    vkCmdSetStencilWriteMask = auto()
    vkCmdSetStencilReference = auto()
    vkCmdBindDescriptorSets = auto()
    vkCmdBindVertexBuffers = auto()
    vkCmdBindIndexBuffer = auto()
    vkCmdCopyBufferToImage = auto()
    vkCmdCopyImageToBuffer = auto()
    vkCmdCopyBuffer = auto()
    vkCmdCopyImage = auto()
    vkCmdBlitImage = auto()
    vkCmdResolveImage = auto()
    vkCmdUpdateBuffer = auto()
    vkCmdFillBuffer = auto()
    vkCmdPushConstants = auto()
    vkCmdClearColorImage = auto()
    vkCmdClearDepthStencilImage = auto()
    vkCmdClearAttachments = auto()
    vkCmdPipelineBarrier = auto()
    vkCmdWriteTimestamp = auto()
    vkCmdCopyQueryPoolResults = auto()
    vkCmdBeginQuery = auto()
    vkCmdEndQuery = auto()
    vkCmdResetQueryPool = auto()
    vkCmdSetEvent = auto()
    vkCmdResetEvent = auto()
    vkCmdWaitEvents = auto()
    vkCmdDraw = auto()
    vkCmdDrawIndirect = auto()
    vkCmdDrawIndexed = auto()
    vkCmdDrawIndexedIndirect = auto()
    vkCmdDispatch = auto()
    vkCmdDispatchIndirect = auto()
    vkCmdDebugMarkerBeginEXT = auto()
    vkCmdDebugMarkerInsertEXT = auto()
    vkCmdDebugMarkerEndEXT = auto()
    vkDebugMarkerSetObjectNameEXT = auto()
    vkCreateSwapchainKHR = auto()
    SetShaderDebugPath = auto()
    vkRegisterDeviceEventEXT = auto()
    vkRegisterDisplayEventEXT = auto()
    vkCmdIndirectSubCommand = auto()
    vkCmdPushDescriptorSetKHR = auto()
    vkCmdPushDescriptorSetWithTemplateKHR = auto()
    vkCreateDescriptorUpdateTemplate = auto()
    vkUpdateDescriptorSetWithTemplate = auto()
    vkBindBufferMemory2 = auto()
    vkBindImageMemory2 = auto()
    vkCmdWriteBufferMarkerAMD = auto()
    vkSetDebugUtilsObjectNameEXT = auto()
    vkQueueBeginDebugUtilsLabelEXT = auto()
    vkQueueEndDebugUtilsLabelEXT = auto()
    vkQueueInsertDebugUtilsLabelEXT = auto()
    vkCmdBeginDebugUtilsLabelEXT = auto()
    vkCmdEndDebugUtilsLabelEXT = auto()
    vkCmdInsertDebugUtilsLabelEXT = auto()
    vkCreateSamplerYcbcrConversion = auto()
    vkCmdSetDeviceMask = auto()
    vkCmdDispatchBase = auto()
    vkGetDeviceQueue2 = auto()
    vkCmdDrawIndirectCount = auto()
    vkCmdDrawIndexedIndirectCount = auto()
    vkCreateRenderPass2 = auto()
    vkCmdBeginRenderPass2 = auto()
    vkCmdNextSubpass2 = auto()
    vkCmdEndRenderPass2 = auto()
    vkCmdBindTransformFeedbackBuffersEXT = auto()
    vkCmdBeginTransformFeedbackEXT = auto()
    vkCmdEndTransformFeedbackEXT = auto()
    vkCmdBeginQueryIndexedEXT = auto()
    vkCmdEndQueryIndexedEXT = auto()
    vkCmdDrawIndirectByteCountEXT = auto()
    vkCmdBeginConditionalRenderingEXT = auto()
    vkCmdEndConditionalRenderingEXT = auto()
    vkCmdSetSampleLocationsEXT = auto()
    vkCmdSetDiscardRectangleEXT = auto()
    DeviceMemoryRefs = auto()
    vkResetQueryPool = auto()
    ImageRefs = auto()
    vkCmdSetLineStippleEXT = auto()
    vkGetSemaphoreCounterValue = auto()
    vkWaitSemaphores = auto()
    vkSignalSemaphore = auto()
    vkQueuePresentKHR = auto()
    vkCmdSetCullModeEXT = auto()
    vkCmdSetFrontFaceEXT = auto()
    vkCmdSetPrimitiveTopologyEXT = auto()
    vkCmdSetViewportWithCountEXT = auto()
    vkCmdSetScissorWithCountEXT = auto()
    vkCmdBindVertexBuffers2EXT = auto()
    vkCmdSetDepthTestEnableEXT = auto()
    vkCmdSetDepthWriteEnableEXT = auto()
    vkCmdSetDepthCompareOpEXT = auto()
    vkCmdSetDepthBoundsTestEnableEXT = auto()
    vkCmdSetStencilTestEnableEXT = auto()
    vkCmdSetStencilOpEXT = auto()
    CoherentMapWrite = auto()
    Max = auto()

pp = pprint.PrettyPrinter(indent=4)

g_is_binding_fbo = True # using this variable to separate passes
g_next_draw_will_add_state = False # using this variable to separate passes
g_markers = []
g_draw_durations = {}

# raw data
g_events = []

html_head = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Render Doctor Analysis</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js"></script>
<style>
        /* Global styles */
        /* Frame Overview table styles */
        .frame-overview-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            font-size: 12px;
        }
        .frame-overview-table th {
            background-color: #ff6600;
            color: white;
            font-weight: 600;
            padding: 8px 4px;
            text-align: center;
            border: 1px solid #e0e0e0;
            font-size: 11px;
        }
        .frame-overview-table td {
            padding: 6px 4px;
            border: 1px solid #e0e0e0;
            text-align: center;
            vertical-align: middle;
            font-size: 11px;
        }
        .frame-overview-table .summary-row {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        .frame-overview-table .pass-header {
            background-color: #e3f2fd;
            font-weight: bold;
        }
        .frame-overview-table .state-row {
            background-color: white;
        }
        .frame-overview-table .state-row:hover {
            background-color: #f5f5f5;
        }
        .depth-preview, .color-preview {
            width: 20px;
            height: 15px;
            border: 1px solid #ddd;
            background: #f0f0f0;
            display: inline-block;
        }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            line-height: 1.6;
        }
        /* Main content area */
        .main-content {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        /* General card styles */
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin: 20px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        /* Pass section styles */
        .pass-section { 
            background: white;
            border-radius: 16px;
            box-shadow: 0 6px 25px rgba(0,0,0,0.1);
            margin: 25px 0;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 2px solid transparent;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            position: relative;
        }
        .pass-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        }
        .pass-section:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            border-color: rgba(102, 126, 234, 0.3);
        }
        .pass-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 20px;
            font-size: 18px;
            font-weight: 600;
            position: relative;
            overflow: hidden;
        }
        .pass-header::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            transform: skewX(-15deg);
        }
        .pass-content-area {
            padding: 25px 20px;
            background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
            position: relative;
        }
        .pass-content-area::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(102, 126, 234, 0.2) 50%, transparent 100%);
        }
        .pass-title {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
            z-index: 1;
        }
        .pass-stats {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            position: relative;
            z-index: 1;
        }
        .stat-item {
            background: rgba(255, 255, 255, 0.25);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .stat-item:hover {
            background: rgba(255, 255, 255, 0.35);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        /* 其余已有样式保持不变 */
</style>



</head>
<body>
"""

html_minimalist_head = """
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js"></script>
<style>
h1 {
    color: #ff6600;
}
.title {
    background-color: #ff6600;
}
</style>
"""

html_lite_head = """
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js"></script>
"""

mermaid_head = """
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>\n
"""

rdc_file = '.rdc'
sdfile = None
class TextureTip:
    def __init__(self, controller, resource_id):
        self.resource_id = resource_id
        self.name = get_resource_name(controller, resource_id, True)
        self.info = get_texture_info(controller, resource_id)
        self.channels = self.info.format.compCount
        self.format = rd.ResourceFormat(self.info.format).Name()

        self.tips = []

        # doctor jobs...
        if self.info.creationFlags & rd.TextureCategory.ColorTarget:
            if 'R16G16B16A16_FLOAT' in self.format:
                self.tips.append('64bits_per_pixel')
        name_lower = self.name.lower()
        if 'hud' in name_lower or 'sactx' in name_lower or 'font' in name_lower or 't_fx' in name_lower or 'tex_eft' in name_lower:
            # white-list, "2D" textures, used as HUD, UI etc.
            pass
        elif self.info.creationFlags == rd.TextureCategory.ShaderRead:
            if config['WRITE_SINGLE_COLOR']:
                # read-only texture
                pixels = controller.GetTextureData(resource_id, rd.Subresource(0, 0, 0))

                is_single_color = True
                fmt = self.info.format
                stride = fmt.compByteWidth * fmt.compCount
                if fmt.compByteWidth == 1 and fmt.compType == rd.CompType.UNorm:
                    unpack_string = 'B' * fmt.compCount
                # elif fmt.compByteWidth == 0 and fmt.compType == rd.CompType.UNorm:
                #     stride = 1 * fmt.compCount
                #     unpack_string = 'B' * fmt.compCount
                elif fmt.compByteWidth == 2 and fmt.compType == rd.CompType.Float:
                    unpack_string = 'e' * fmt.compCount
                elif fmt.compByteWidth == 4 and fmt.compType == rd.CompType.Float:
                    unpack_string = 'f' * fmt.compCount
                else:
                    unpack_string = ''

                if unpack_string:
                    prev_pixel = struct.unpack_from(unpack_string, pixels, 0)
                    for i in range(self.info.width * self.info.height):
                        pixel = struct.unpack_from(unpack_string, pixels, i * stride)
                        if prev_pixel != pixel:
                            is_single_color = False
                            break
                        prev_pixel = pixel

                    if is_single_color:
                        self.tips.append('single_color' + str(prev_pixel))

            if 'lightmap' not in name_lower and (self.info.width > 512 or self.info.height > 512):
                self.tips.append('large_dimension')
            if self.info.width >= 256 and self.info.height >= 256:
                if self.info.mips == 1:
                    self.tips.append('no_mipmap')
                if 'BC' not in self.format and\
                    'ETC' not in self.format and\
                    'EAC' not in self.format and\
                    'ASTC' not in self.format and\
                    'PVRTC' not in self.format:
                    self.tips.append('uncompressed_format')
                if not math.log(self.info.width, 2).is_integer() or\
                    not math.log(self.info.height, 2).is_integer():
                    self.tips.append('not_power_of_two')

            # if tex_info.creationFlags != rd.TextureCategory.ShaderRead:
            # continue

class ShaderDoctor:
    def __init__(self, controller, resource_id):
        pass

'''
PSD (Pass - State - Draw) hierachy, there could be other hierachies, so I need to separate <derived data> from <raw data>

Frame
    - Pass
        - State
            - Draw
                - Event
                - Event
                - Event
            - Draw
            - Draw
        - State
        - State
    - Pass
    - Pass
'''

class Pass:
    # draws on same FBO
    def __init__(self):
        self.pass_id = Pass.s_id
        Pass.s_id += 1
        self.states = []

    def addState(self, draw):
        # if len(self.states) > 0 and self.states[0].getName().find('s_') == 0:
        #     # dummy, replace it
        #     self.states[0] = State(draw)
        #     return

        # print("addState %d" % (len(self.states)))

        new_state = State(draw)
        self.states.append(new_state)
        State.current = self.states[-1]

    def getFirstDraw(self):
        # TODO: this is a wrong assumption, fix it when I have time
        if len(self.states) == 0:
            return None
        return self.states[0].getFirstDraw()

    def getLastDraw(self):
        # TODO: this is a wrong assumption, fix it when I have time
        if len(self.states) == 0:
            return None
        return self.states[-1].getLastDraw()

    def getName(self, controller):
        if self.name:
            return self.name

        pass_info = ''
        if self.getLastDraw():
            # TODO: assume every draws share the same set of targets
            pass_info = self.getLastDraw().getPassSummary(controller)

        if not pass_info:
            self.name = 'Pass%d' % (self.pass_id)
        else:
            self.name = 'Pass%d_%s' % (self.pass_id, pass_info)

        return self.name

    def writeIndexHtml(self, html_file, controller):
        pass_name = self.getName(controller)
        
        # 计算Pass统计信息
        total_draws = len(self.states)
        total_shaders = 0
        total_textures = 0
        
        # 安全地计算统计信息
        for s in self.states:
            if hasattr(s, 'draws') and s.draws:
                # 检查绘制调用中的着色器
                for draw in s.draws:
                    if hasattr(draw, 'shader_names') and draw.shader_names:
                        total_shaders += 1
                    if hasattr(draw, 'textures') and draw.textures:
                        total_textures += len(draw.textures)
        
        # Pass section with enhanced card layout
        html_file.write('<div class="pass-section">\n')
        html_file.write('<div class="pass-header">\n')
        html_file.write('<div class="pass-title">🎯 %s</div>\n' % pass_name)
        html_file.write('<div class="pass-stats">\n')
        html_file.write('<span class="stat-item">📊 绘制调用: %d</span>\n' % total_draws)
        html_file.write('<span class="stat-item">🔧 着色器: %d</span>\n' % total_shaders)
        html_file.write('<span class="stat-item">🖼️ 贴图: %d</span>\n' % total_textures)
        html_file.write('</div>\n')
        html_file.write('</div>\n')
        
        html_file.write('<div class="pass-content-area">\n')
        
        # 按状态分组显示
        state_groups = {}
        for s in self.states:
            state_key = s.getName()
            if state_key not in state_groups:
                state_groups[state_key] = []
            state_groups[state_key].append(s)
        
        for state_name, states in state_groups.items():
            if len(states) > 1:
                # 多个相同状态的绘制调用
                html_file.write('<div class="state-group">\n')
                html_file.write('<div class="state-group-header">\n')
                html_file.write('<h4>🔧 %s (%d个调用)</h4>\n' % (state_name, len(states)))
                html_file.write('</div>\n')
                html_file.write('<div class="state-group-content">\n')
                for s in states:
                    s.writeIndexHtml(html_file, controller)
                html_file.write('</div>\n')
                html_file.write('</div>\n')
            else:
                # 单个绘制调用
                states[0].writeIndexHtml(html_file, controller)
        
        html_file.write('</div>\n')
        html_file.write('</div>\n')

    def exportResources(self, controller):
        for s in self.states:
            s.exportResources(controller)

    def writeDetailHtml(self, html_file, controller):
        for s in self.states:
            filename = g_assets_folder / (s.getUniqueName() + '.html')
            if not Path(filename).exists():
                with open(filename,"w") as self_html:
                    s.writeDetailHtml(self_html, controller)
                    print(filename)

    states = None
    pass_id = None
    current = None
    name = None
    s_id = 1

uniqueStateCounters = {}

class State:
    def __init__(self, draw):
        self.events = []
        self.draws = []
        self.name = 'default'
        self.unique_name = self.name
        # TODO: refactor
        self.vs_name = ''
        self.ps_name = ''
        self.cs_name = ''
        State.s_id += 1

        if draw:
            self.name = draw.state_key
            self.vs_name = draw.short_shader_names[rd.ShaderStage.Vertex]
            self.ps_name = draw.short_shader_names[rd.ShaderStage.Pixel]
            self.cs_name = draw.short_shader_names[rd.ShaderStage.Compute]

            if self.name in uniqueStateCounters:
                uniqueStateCounters[self.name] += 1
                self.unique_name = '%s_%d' % (self.name, uniqueStateCounters[self.name])
            else:
                uniqueStateCounters[self.name] = 0
                self.unique_name = self.name

    def getFirstDraw(self):
        if len(self.draws) == 0:
            return None

        return self.draws[0]

    def getLastDraw(self):
        if len(self.draws) == 0:
            return None

        return self.draws[-1]

    def getUniqueName(self):
        # used in HTML annotation
        return self.unique_name

    def getName(self):
        return self.name

    def writeIndexHtml(self, html_file, controller):
        html_file.write('<div class="state-section">\n')
        html_file.write('<h3>🔧 %s</h3>\n' % self.getUniqueName())
        html_file.write('</div>\n')
        # for ev in self.events:
        #     ev.writeIndexHtml(html_file, controller)
        draw_count = len(self.draws)
        if draw_count == 0:
            return
        if config['MINIMALIST']:
            # MINIMALIST only cares about last draw
            self.draws[-1].writeIndexHtml(html_file, controller)
            return

        if draw_count == 1:
            self.draws[0].writeIndexHtml(html_file, controller)
        elif draw_count == 2:
            self.draws[0].writeIndexHtml(html_file, controller)
            self.draws[1].writeIndexHtml(html_file, controller)
        else:
            self.draws[0].writeIndexHtml(html_file, controller)
            self.draws[int(draw_count/2)].writeIndexHtml(html_file, controller)
            self.draws[-1].writeIndexHtml(html_file, controller)

        html_file.write('\n')

    def writeDetailHtml(self, html_file, controller):
        html_file.write('<!DOCTYPE html>\n<html>\n<head>\n')
        html_file.write('<meta charset="utf-8">\n')
        html_file.write('<title>渲染医生 - 美术资产分析</title>\n')
        html_file.write('<style>\n')
        html_file.write('body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }\n')
        html_file.write('.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; }\n')
        html_file.write('.header h1 { margin: 0; font-size: 28px; }\n')
        html_file.write('.header p { margin: 5px 0 0 0; opacity: 0.9; }\n')
        html_file.write('.content { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }\n')
        html_file.write('.draw-call { margin: 20px 0; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; background: #fafafa; }\n')
        html_file.write('.draw-call h3 { margin: 0 0 15px 0; color: #333; font-size: 18px; }\n')
        html_file.write('.marker { background: #fff3cd; color: #856404; padding: 8px 12px; border-radius: 6px; margin: 10px 0; font-weight: 500; }\n')
        html_file.write('.call-type { background: #d1ecf1; color: #0c5460; padding: 8px 12px; border-radius: 6px; margin: 10px 0; font-weight: 500; }\n')
        html_file.write('.pipeline-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 15px 0; }\n')
        html_file.write('.info-item { background: white; padding: 8px 12px; border-radius: 6px; border: 1px solid #e0e0e0; }\n')
        html_file.write('.shader-section, .constant-buffer { margin: 15px 0; }\n')
        html_file.write('.shader-section h4, .constant-buffer h4 { margin: 0 0 10px 0; color: #555; font-size: 16px; }\n')
        html_file.write('.shader-item { background: white; padding: 8px 12px; border-radius: 6px; border: 1px solid #e0e0e0; margin: 5px 0; }\n')
        html_file.write('.shader-item a { color: #0066cc; text-decoration: none; }\n')
        html_file.write('.shader-item a:hover { color: #ff6600; }\n')
        html_file.write('.texture-section { margin: 20px 0; }\n')
        html_file.write('.texture-section h4 { margin: 0 0 15px 0; color: #555; font-size: 16px; }\n')
        html_file.write('.events-section { margin: 20px 0; }\n')
        html_file.write('.events-section h4 { margin: 0 0 15px 0; color: #555; font-size: 16px; }\n')
        html_file.write('.event-item { background: #f8f9fa; padding: 8px 12px; border-radius: 6px; margin: 5px 0; font-family: monospace; font-size: 14px; }\n')
        html_file.write('</style>\n')
        html_file.write('</head>\n<body>\n')
        html_file.write('<div class="header">\n')
        html_file.write('<h1>🎨 渲染医生 - 美术资产分析</h1>\n')
        html_file.write('<p>基于实际渲染资源的详细分析报告</p>\n')
        html_file.write('</div>\n')
        html_file.write('<div class="content">\n')
        for d in self.draws:
            d.writeDetailHtml(html_file, controller)
        html_file.write('</div>\n')
        html_file.write('</body>\n')

        html_file.write('</html>')

    def exportResources(self, controller):
        if config['WRITE_ALL_DRAWS']:
            for d in self.draws:
                d.exportResources(controller)
        else:
            draw_count = len(self.draws)
            if draw_count == 0:
                return
            if config['MINIMALIST']:
                # MINIMALIST only cares about last draw
                self.draws[-1].exportResources(controller)
                return

            if draw_count == 1:
                self.draws[0].exportResources(controller)
            elif draw_count == 2:
                self.draws[0].exportResources(controller)
                self.draws[1].exportResources(controller)
            else:
                self.draws[0].exportResources(controller)
                self.draws[int(draw_count/2)].exportResources(controller)
                self.draws[-1].exportResources(controller)

    def addEvent(self, ev):
        self.events.append(ev)

    def addDraw(self, draw):
        self.events.append(draw)
        self.draws.append(draw)

    current = None
    events = None
    draws = None
    s_id = 0

State.default = State(None)

class Event:
    def __init__(self, controller, ev, level = 0):
        global g_is_binding_fbo
        global api_full_log
        global api_short_log
        global g_next_draw_will_add_state
        chunks = sdfile.chunks
        self.chunk_id = ev.chunkIndex
        self.event_id = ev.eventId
        self.level = level
        # m_StructuredFile->chunks[ev.chunkIndex]->metadata.chunkID
        # C:\svn_pool\renderdoc\renderdoc\driver\gl\gl_driver.cpp

        # struct SDChunkMetaData
        # enum class GLChunk
        self.event_type = None  # 初始化event_type
        try:
            if ev.chunkIndex < len(chunks):
                cid = chunks[ev.chunkIndex].metadata.chunkID
                if API_TYPE == rd.GraphicsAPI.OpenGL:
                    self.event_type = GLChunk(cid)
                elif API_TYPE == rd.GraphicsAPI.Vulkan:
                    self.event_type = VulkanChunk(cid)
                else:
                    self.event_type = D3D11Chunk(cid)
                self.name = self.event_type.name
            else:
                print(f"Debug: chunkIndex {ev.chunkIndex} out of range for chunks (length: {len(chunks)})")
                self.name = "Unknown"
        except Exception as e:
            print(f"Debug: Error processing event {ev.eventId}: {e}")
            self.name = "Error"

        if self.name.find('Draw') != -1 \
            or self.name.find('Dispatch') != -1:
            g_is_binding_fbo = False
        else:
            api_full_log.write('%s%04d %s\n' % ('    ' * level, self.event_id, self.name))
            if self.event_type and (self.event_type == GLChunk.glBindFramebuffer or \
                self.event_type == VulkanChunk.vkCmdBeginRenderPass or \
                self.event_type == D3D11Chunk.OMSetRenderTargets or \
                self.event_type == D3D11Chunk.OMSetRenderTargetsAndUnorderedAccessViews):
                if not g_is_binding_fbo:
                    # non fbo call -> fbo call, marks start of a new pass
                    api_short_log.write('%se%04d %s\n' % ('    ' * level, self.event_id, self.name))
                    g_next_draw_will_add_state = True
                g_is_binding_fbo = True

    def writeIndexHtml(self, markdown, controller):
        pass

    def exportResources(self, controller):
        pass

    name = None
    event_id = None
    level = None
    event_type = None
    chunk_id = None

class Draw(Event):
    def __init__(self, controller, draw, level = 0):
        try:
            global api_full_log
            global api_short_log
            action_name = draw.GetName(sdfile)
            print('draw %d: %s\n' % (draw.actionId, action_name))
            api_full_log.write('%sdraw_%04d %s\n' % ('    ' * level, draw.actionId, action_name))
            api_short_log.write('%s%04d %s\n' % ('    ' * level, draw.actionId, action_name))
            self.draw_desc = draw
            self.event_id = draw.eventId
            self.draw_id = draw.actionId
            self.name = action_name # TODO:
            self.level = level
            self.state_key = ''
            print(f"Debug: Initializing Draw for event {self.event_id}, action {self.draw_id}")
            self.short_shader_names = [None] * rd.ShaderStage.Count
            self.shader_names = [None] * rd.ShaderStage.Count
            self.shader_cb_contents = [None] * rd.ShaderStage.Count
        except Exception as e:
            print(f"Debug: Error in Draw.__init__: {e}")
            import traceback
            traceback.print_exc()
            raise
        self.textures = []
        self.color_buffers = []
        self.depth_buffer = None
        self.expanded_marker = get_expanded_marker_name()
        self.marker = get_marker_name()
        self.gpu_duration = 0

        self.alpha_enabled = False
        self.depth_state = [' '] * 3
        self.write_mask = [' '] * 4

        if self.event_id in g_draw_durations:
            self.gpu_duration = g_draw_durations[self.event_id]
            if math.isnan(self.gpu_duration) or self.gpu_duration < 0:
                self.gpu_duration = 0

        for output in draw.outputs:
            self.color_buffers.append(output)
        self.depth_buffer = draw.depthOut

        # api_full_log.flush()
        # api_short_log.flush()

    def sharesState(self, other):
        if self.depth_buffer != other.depth_buffer:
            return False
        if len(self.color_buffers) != len(other.color_buffers):
            return False
        for i in range(0, len(self.color_buffers)):
            if self.color_buffers[i] != other.color_buffers[i]:
                return False

        return True

    def isClear(self):
        return 'Clear' in self.name\
            or 'Invalidate' in self.name \
            or 'Discard' in self.name

    def isCopy(self):
        return 'Copy' in self.name

    def isDispatch(self):
        return self.name.find('Dispatch') != -1

    def collectPipeline(self, controller):
        if not config['WRITE_PIPELINE']:
            return

        if self.isClear():
            self.state_key = 'Clear'

            if self.state_key != State.current.getName():
                # detects a PSO change
                # TODO: this is too ugly
                # TODO: this is double double ugly
                Pass.current.addState(self)
            return

        if self.isCopy():
            self.state_key = 'Copy'

            if self.state_key != State.current.getName():
                Pass.current.addState(self)
            return

        global api_full_log

        if API_TYPE == rd.GraphicsAPI.Vulkan and self.isDispatch():
            # on Android devices, Vulkan dispatch calls will likely crash renderdoc, so we skip them
            self.state_key = 'compute_shader'
            if self.state_key != State.current.getName():
                Pass.current.addState(self)
            return

        controller.SetFrameEvent(self.event_id, False)
        api_state = None
        pipe_state : rd.PipeState = controller.GetPipelineState()

        if API_TYPE == rd.GraphicsAPI.OpenGL:
            api_state = controller.GetGLPipelineState()
            # C:\svn_pool\renderdoc\renderdoc\api\replay\gl_pipestate.h
        elif API_TYPE == rd.GraphicsAPI.D3D11:
            api_state = controller.GetD3D11PipelineState()
        elif API_TYPE == rd.GraphicsAPI.D3D12:
            api_state = controller.GetD3D12PipelineState()
        elif API_TYPE == rd.GraphicsAPI.Vulkan:
            api_state = controller.GetVulkanPipelineState()

        program_name = ""

        shader_flags = [
            '--vertex',
            '--tessellation_control',
            '--tessellation_evaluation',
            '--geometry',
            '--fragment',
            '--compute',
        ]
        # Ensure shader_flags has enough elements for all shader stages
        print(f"Debug: rd.ShaderStage.Count = {rd.ShaderStage.Count}")
        print(f"Debug: Original shader_flags length = {len(shader_flags)}")
        
        # Unity specific handling
        if rd.ShaderStage.Count > 6:
            print(f"Debug: Unity detected - extended shader stages: {rd.ShaderStage.Count}")
            # Unity may use custom shader stages or extended pipeline
            for i in range(6, rd.ShaderStage.Count):
                shader_flags.append(f'--unity_stage_{i}')
        
        while len(shader_flags) < rd.ShaderStage.Count:
            shader_flags.append('--unknown')
        print(f"Debug: Extended shader_flags length = {len(shader_flags)}")
        for stage in range(0, rd.ShaderStage.Count):
            # C:\svn_pool\renderdoc\renderdoc\api\replay\shader_types.h
            # struct ShaderReflection
            # TODO: refactor
            shader = None
            shader_name = None
            short_shader_name = None
            refl = None
            shader_id = pipe_state.GetShader(stage)

            if self.isDispatch():
                if stage != 5:
                    continue
                shader = api_state.computeShader
            else:
                if stage == 0:
                    shader = api_state.vertexShader
                elif stage == 1:
                    if API_TYPE == rd.GraphicsAPI.OpenGL or API_TYPE == rd.GraphicsAPI.Vulkan:
                        shader = api_state.tessControlShader
                    else:
                        shader = api_state.hullShader
                elif stage == 2:
                    if API_TYPE == rd.GraphicsAPI.OpenGL or API_TYPE == rd.GraphicsAPI.Vulkan:
                        shader = api_state.tessEvalShader
                    else:
                        shader = api_state.domainShader
                elif stage == 3:
                    shader = api_state.geometryShader
                elif stage == 4:
                    if API_TYPE == rd.GraphicsAPI.OpenGL or API_TYPE == rd.GraphicsAPI.Vulkan:
                        shader = api_state.fragmentShader
                    else:
                        shader = api_state.pixelShader
                elif stage == 5:
                    continue

            # TODO: improve the logic among program_name, short_shader_name and shader_name
            if shader_id != rd.ResourceId.Null():
                # api_full_log.write(str(shader_id))
                # api_full_log.write('\n')
                refl = pipe_state.GetShaderReflection(stage)
                if hasattr(shader, 'programResourceId'):
                    # Opengl
                    program_name = get_resource_name(controller, shader.programResourceId)
                    short_shader_name = get_resource_name(controller, shader.shaderResourceId)
                    shader_name = program_name + '_' + short_shader_name
                elif hasattr(api_state, 'pipelineResourceId'):
                    # DX12
                    program_name = get_resource_name(controller, api_state.pipelineResourceId)
                    program_name = program_name.replace('Pipeline_State', 'pso')
                    short_shader_name = get_resource_name(controller, shader_id)
                    shader_name = program_name + '_' + short_shader_name
                elif hasattr(api_state, 'graphics') or hasattr(api_state, 'compute'):
                    # Vulkan
                    p = api_state.graphics or api_state.graphics
                    program_name = get_resource_name(controller, p.pipelineResourceId)
                    program_name = program_name.replace('Pipeline', 'pso')
                    short_shader_name = get_resource_name(controller, shader_id)
                    # .replace('Shader_Module', 'shader')
                    if 'Shader_Module' in short_shader_name:
                        shader_name = program_name + '_' + ShaderStage(stage).name
                    else:
                        program_name = short_shader_name 
                        shader_name = short_shader_name + '_' + ShaderStage(stage).name
                else:
                    short_shader_name = get_resource_name(controller, shader_id)
                    short_shader_name = short_shader_name.replace('Vertex_Shader', 'vs').replace('Pixel_Shader', 'ps').replace('Compute_Shader', 'cs').replace('Shader_Module', 'shader').replace('Geometry_Shader', 'gs')
                    if program_name and short_shader_name not in program_name:
                            # Skip duplicated shader names in same program
                            program_name += '_'
                            program_name += short_shader_name
                    else:
                        program_name = 's_' + short_shader_name
                    shader_name = short_shader_name
                self.shader_names[stage] = shader_name
                self.short_shader_names[stage] = short_shader_name

            if refl:
                if config['WRITE_CONST_BUFFER']:
                    self.shader_cb_contents[stage] = get_cbuffer_contents(controller, stage, self.shader_names[stage], refl, program_name)

                    # const_buffer--%4d.html
                    resource_name = 'const_buffer--%04d' % (self.draw_id)
                    file_name = g_assets_folder / get_resource_filename(resource_name, 'html')
                    with open(file_name, 'w', encoding='utf-8') as fp:
                        fp.write('<!DOCTYPE html>\n<html>\n<head>\n')
                        fp.write('<meta charset="utf-8">\n')
                        fp.write('<title>Constant Buffer Analysis</title>\n')
                        fp.write('<style>\n')
                        fp.write('body { font-family: Arial, sans-serif; margin: 20px; }\n')
                        fp.write('.cb-header { background-color: #ff6600; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }\n')
                        fp.write('.cb-section { background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #ff6600; }\n')
                        fp.write('.cb-code { background-color: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: "Courier New", monospace; }\n')
                        fp.write('</style>\n')
                        fp.write('</head>\n<body>\n')
                        
                        fp.write('<div class="cb-header">\n')
                        fp.write('<h1>📊 Constant Buffer Analysis</h1>\n')
                        fp.write('<p>Draw ID: %04d</p>\n' % self.draw_id)
                        fp.write('</div>\n')
                        
                        for s in range(0, rd.ShaderStage.Count):
                            if s < len(self.shader_cb_contents) and self.shader_cb_contents[s]:
                                fp.write('<div class="cb-section">\n')
                                fp.write('<h2>🎯 %s Shader</h2>\n' % (ShaderStage(s).name))
                                fp.write('<div class="cb-code">\n')
                                fp.write('<pre>%s</pre>\n' % self.shader_cb_contents[s])
                                fp.write('</div>\n')
                                fp.write('</div>\n')
                        
                        fp.write('</body>\n</html>')
                if False:
                    # TODO: sadly ShaderBindpointMapping is always empty :(
                    try:
                        if hasattr(shader, 'bindpointMapping'):
                            mapping = shader.bindpointMapping # struct ShaderBindpointMapping
                            for sampler in mapping.samplers:
                                print(sampler.name)
                    except AttributeError:
                        print(f"Debug: Shader object has no attribute 'bindpointMapping'")
                        pass

                if False:
                    samplers = pipe_state.GetSamplers(stage)
                    for sampler in samplers:
                        print(sampler)

                # raw txt
                txt_file_name = get_resource_filename(g_assets_folder / shader_name, 'txt')

                if not Path(txt_file_name).exists():
                    with open(txt_file_name, 'wb') as fp:
                        print("Writing %s" % txt_file_name)
                        fp.write(refl.rawBytes)

                # html
                html_file_name = get_resource_filename(g_assets_folder / shader_name, 'html')
                if not Path(html_file_name).exists():
                    highlevel_shader = ''
                    shader_analysis = ''
                    if API_TYPE == rd.GraphicsAPI.OpenGL or API_TYPE == rd.GraphicsAPI.Vulkan:
                        if API_TYPE == rd.GraphicsAPI.OpenGL:
                            highlevel_shader = str(refl.rawBytes, 'utf-8')
                            highlevel_shader = highlevel_shader.replace('<', ' < ') # fix a glsl syntax bug
                            lang = '--opengles'
                        else:
                            targets = controller.GetDisassemblyTargets(True)
                            for t in targets:
                                highlevel_shader = controller.DisassembleShader(pipe_state.GetGraphicsPipelineObject(), refl, t)
                                break
                            lang = '--vulkan'

                        malioc_exe = g_assets_folder / '../' / 'mali_offline_compiler/malioc.exe'
                        if config['WRITE_MALIOC'] and  malioc_exe.exists():
                            # Define shader_flags locally to avoid conflicts
                            local_shader_flags = [
                                '--vertex',
                                '--tessellation_control',
                                '--tessellation_evaluation',
                                '--geometry',
                                '--fragment',
                                '--compute',
                            ]
                            # Ensure stage is within bounds
                            if stage < len(local_shader_flags):
                                stage_flag = local_shader_flags[stage]
                            else:
                                stage_flag = '--unknown'
                                print(f"Debug: Stage {stage} out of range for shader_flags (length: {len(local_shader_flags)})")
                            args = [
                                str(malioc_exe),
                                stage_flag,
                                lang,
                                txt_file_name
                            ]
                            proc = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True)
                            shader_analysis, _ = proc.communicate()
                            shader_analysis = str(shader_analysis, 'utf-8')
                            shader_analysis = shader_analysis.replace('\r\n\r\n', '\n')
                    else:
                        targets = controller.GetDisassemblyTargets(True)
                        for t in targets:
                            highlevel_shader = controller.DisassembleShader(pipe_state.GetGraphicsPipelineObject(), refl, t)
                            break

                    with open(html_file_name, 'w', encoding='utf-8') as fp:
                        print("Writing %s" % html_file_name)
                        fp.write('<!DOCTYPE html>\n<html>\n<head>\n')
                        fp.write('<meta charset="utf-8">\n')
                        fp.write('<title>Shader Analysis</title>\n')
                        fp.write('<style>\n')
                        fp.write('body { font-family: Arial, sans-serif; margin: 20px; }\n')
                        fp.write('.shader-header { background-color: #ff6600; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }\n')
                        fp.write('.shader-content { background-color: #f8f8f8; padding: 15px; border-radius: 5px; border-left: 4px solid #ff6600; }\n')
                        fp.write('.shader-code { background-color: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: "Courier New", monospace; }\n')
                        fp.write('.analysis-section { background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 10px 0; }\n')
                        fp.write('</style>\n')
                        fp.write('</head>\n<body>\n')
                        
                        # Marker section
                        if self.expanded_marker:
                            fp.write('<div class="shader-header">\n')
                            fp.write('<h2>🔍 Marker: %s</h2>\n' % self.expanded_marker)
                            fp.write('</div>\n')
                        
                        # Analysis section
                        if shader_analysis:
                            fp.write('<div class="analysis-section">\n')
                            fp.write('<h3>📊 Shader Analysis</h3>\n')
                            fp.write('<pre>%s</pre>\n' % shader_analysis)
                            fp.write('</div>\n')
                        
                        # Shader code section
                        fp.write('<div class="shader-content">\n')
                        fp.write('<h3>💻 Shader Code</h3>\n')
                        fp.write('<div class="shader-code">\n')
                        fp.write('<pre>%s</pre>\n' % highlevel_shader)
                        fp.write('</div>\n')
                        fp.write('</div>\n')
                        
                        fp.write('</body>\n</html>')

                # C:\svn_pool\renderdoc\renderdoc\api\replay\gl_pipestate.h
                # struct State

                # TODO: deal with other resources, (atomicBuffers, uniformBuffers, shaderStorageBuffers, images, transformFeedback etc)
                if API_TYPE == rd.GraphicsAPI.D3D11:
                    try:
                        if hasattr(shader, 'bindpointMapping'):
                            mapping = shader.bindpointMapping # struct ShaderBindpointMapping
                            for sampler in mapping.readOnlyResources:
                                # print(sampler.bind, sampler.bindset)
                                srv = shader.srvs[sampler.bind]
                                resource_id = srv.resourceResourceId
                                if resource_id == rd.ResourceId.Null():
                                    continue
                                g_frame.textures.add(resource_id)
                                self.textures.append(resource_id)
                    except AttributeError:
                        print(f"Debug: D3D11Shader object has no attribute 'bindpointMapping'")
                        pass
                elif API_TYPE == rd.GraphicsAPI.Vulkan and not self.textures:
                    for desc_set in api_state.graphics.descriptorSets:
                        for binding in desc_set.bindings:
                            for bind in binding.binds:
                                # print(bind.resourceResourceId, str(bind.viewFormat))
                                resource_id = bind.resourceResourceId
                                if resource_id == rd.ResourceId.Null():
                                    continue
                                if not get_texture_info(controller, resource_id):
                                    continue
                                g_frame.textures.add(resource_id)
                                self.textures.append(resource_id)

                    for sampler in shader.reflection.readOnlyResources:
                        pass
                        # print(sampler)
                        # srv = api_state.images[sampler.bind]
                        # resource_id = srv.resourceId
                        # if resource_id == rd.ResourceId.Null():
                        #     continue
                        # g_frame.textures.add(resource_id)
                        # self.textures.append(resource_id)
                elif hasattr(api_state, 'textures') and not self.textures:
                    try:
                        if hasattr(shader, 'bindpointMapping'):
                            mapping = shader.bindpointMapping # struct ShaderBindpointMapping
                    except AttributeError:
                        print(f"Debug: Shader object has no attribute 'bindpointMapping'")
                        mapping = None

                    for idx, sampler in enumerate(api_state.samplers):
                        # TODO: why is sampler always zero?
                        resource_id = sampler.resourceId
                        if resource_id == rd.ResourceId.Null():
                            continue
                        # print(sampler.minLOD)

                    for idx, texture in enumerate(api_state.textures):
                        resource_id = texture.resourceId
                        if resource_id == rd.ResourceId.Null():
                            continue
                        g_frame.textures.add(resource_id)
                        self.textures.append(resource_id)
                        

        self.state_key = program_name

        if not self.isDispatch():
            if API_TYPE == rd.GraphicsAPI.OpenGL and self.depth_buffer:
                depthState : rd.GLPipe.DepthState = api_state.depthState
                if depthState.depthEnable: self.depth_state[0] = 'R'
                if depthState.depthWrites: self.depth_state[1] = 'W'
                stencilState : rd.GLPipe.StencilState = api_state.stencilState
                if stencilState.stencilEnable: self.depth_state[2] = '+S'
            elif API_TYPE == rd.GraphicsAPI.Vulkan and self.depth_buffer:
                depthState : rd.VKPipe.DepthStencil = api_state.depthStencil
                if depthState.depthTestEnable: self.depth_state[0] = 'R'
                if depthState.depthWriteEnable: self.depth_state[1] = 'W'
                if depthState.stencilTestEnable: self.depth_state[2] = '+S'
            elif API_TYPE == rd.GraphicsAPI.D3D11 or API_TYPE == rd.GraphicsAPI.D3D12 and self.depth_buffer:
                depthState = api_state.outputMerger.depthStencilState
                if depthState.depthEnable: self.depth_state[0] = 'R'
                if depthState.depthWrites: self.depth_state[1] = 'W'
                if depthState.stencilEnable: self.depth_state[2] = '+S'

            if self.color_buffers and self.color_buffers[0] != rd.ResourceId.Null():
                blends = pipe_state.GetColorBlends()
                for blend in blends:
                    if blend.enabled:
                        self.alpha_enabled = True

                    if blend.writeMask & 0b0001: self.write_mask[0] = 'R'
                    if blend.writeMask & 0b0010: self.write_mask[1] = 'G'
                    if blend.writeMask & 0b0100: self.write_mask[2] = 'B'
                    if blend.writeMask & 0b1000: self.write_mask[3] = 'A'
                    # TODO: support MRT
                    break

        if self.state_key != State.current.getName():
            # detects a PSO change
            # TODO: this is too ugly
            Pass.current.addState(self)

    def getPassSummary(self, controller):
        summary = ''
        color_count = 0
        depth_count = 0
        texture_info = None
        for resource_id in self.color_buffers:
            if resource_id != rd.ResourceId.Null():
                color_count += 1
                if not texture_info:
                    texture_info = get_texture_info(controller, resource_id)
        if self.depth_buffer != rd.ResourceId.Null():
            depth_count += 1
            if not texture_info:
                texture_info = get_texture_info(controller, self.depth_buffer)
        if depth_count > 0:
            summary = 'z'
        else:
            summary = ''
        if color_count > 0:
            if color_count == 1:
                summary += 'c'
            else:
                summary += '%dc' % (color_count)

        if texture_info:
            summary = '%s_%dX%d' % (summary, texture_info.width, texture_info.height)
        return summary

    def writeTextureHtml(self, html_file, controller, caption_suffix, resource_id, texture_file_name):
        texture_info = get_texture_info(controller, resource_id)
        if not texture_info: return
        depth_info = ''
        arraysize_info = ''
        mips_info = ''
        if texture_info.depth > 1:
            depth_info = 'x%d' % texture_info.depth
        if texture_info.arraysize > 1:
            arraysize_info = '[%d]' % texture_info.arraysize
        if texture_info.mips > 1:
            mips_info = '%d mips ' % texture_info.mips
        texture_info_text = '(%dX%d%s%s %s%s)' % (texture_info.width, texture_info.height, depth_info, arraysize_info, mips_info, rd.ResourceFormat(texture_info.format).Name() )

        # enum class ResourceFormatType
        # rdcstr ResourceFormatName(const ResourceFormat &fmt)
        # enum class ResourceFormatType
        # rdcstr ResourceFormatName(const ResourceFormat &fmt)
        # 使用优化的图片标签，支持懒加载和响应式设计
        html_file.write('<div class="texture-container">')
        html_file.write('<img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjVmNWY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlPC90ZXh0Pjwvc3ZnPg==" data-src="assets/%s" alt="%s %s" class="lazyload texture-image" loading="lazy" style="max-width: 200px; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 5px; transition: transform 0.3s ease;">' % (texture_file_name, caption_suffix, texture_info_text))
        html_file.write('<div class="texture-info">%s %s</div>' % (caption_suffix, texture_info_text))
        html_file.write('</div>')

    def writeDetailHtml(self, html_file, controller):
        self.writeIndexHtml(html_file, controller)
        chunks = sdfile.chunks

        html_file.write('<div class="events-section">\n')
        html_file.write('<h4>📋 事件列表</h4>\n')
        for ev in self.draw_desc.events:
            cid = chunks[ev.chunkIndex].metadata.chunkID
            if API_TYPE == rd.GraphicsAPI.OpenGL:
                event_type = GLChunk(cid)
            elif API_TYPE == rd.GraphicsAPI.Vulkan:
                event_type = VulkanChunk(cid)
            else:
                event_type = D3D11Chunk(cid)
            html_file.write('<div class="event-item">event_%04d %s</div>\n' % (ev.eventId, event_type.name))
        html_file.write('</div>\n')

    def writeIndexHtml(self, html_file, controller):
        global g_assets_folder

        html_file.write('<div class="pass-section">\n')
        html_file.write('<div class="pass-header">\n')
        html_file.write('<div class="pass-title">🎯 绘制调用 [D]%04d %s</div>\n' % (self.draw_id, self.name.replace('#', '_')))
        
        # 计算统计信息
        shader_count = sum(1 for name in self.shader_names if name is not None)
        texture_count = len(self.textures) if hasattr(self, 'textures') else 0
        
        html_file.write('<div class="pass-stats">\n')
        html_file.write('<span class="stat-item">🔧 着色器: %d</span>\n' % shader_count)
        html_file.write('<span class="stat-item">🖼️ 贴图: %d</span>\n' % texture_count)
        if self.isClear():
            html_file.write('<span class="stat-item">🧹 清除操作</span>\n')
        elif self.isCopy():
            html_file.write('<span class="stat-item">📋 复制操作</span>\n')
        html_file.write('</div>\n')
        html_file.write('</div>\n')
        
        html_file.write('<div class="pass-content-area">\n')

        if self.expanded_marker:
            html_file.write('<div class="marker">📌 %s</div>\n' % self.expanded_marker)

        if self.isClear() or self.isCopy():
            html_file.write('<div class="call-type">%s</div>\n' % ("清除" if self.isClear() else "复制"))
        else:
            html_file.write('<div class="pipeline-info">\n')
            html_file.write('<div class="info-item"><strong>混合:</strong> %s</div>\n' % ("启用" if self.alpha_enabled else "禁用"))
            html_file.write('<div class="info-item"><strong>深度状态:</strong> %s</div>\n' % ''.join(self.depth_state))
            html_file.write('<div class="info-item"><strong>写入掩码:</strong> %s</div>\n' % ''.join(self.write_mask))
            html_file.write('</div>\n')

            # shader section
            if any(self.shader_names):
                html_file.write('<div class="shader-section">\n')
                html_file.write('<h4>🔧 着色器</h4>\n')
            for stage in range(0, rd.ShaderStage.Count):
                if stage < len(self.shader_names) and self.shader_names[stage] != None:
                        html_file.write('<div class="shader-item">%s: <a href="assets/%s.html">%s</a></div>\n' % (ShaderStage(stage).name, self.shader_names[stage], self.shader_names[stage]))
            html_file.write('</div>\n')

            # cb / constant buffer section
            if config['WRITE_CONST_BUFFER']:
                resource_name = 'const_buffer--%04d' % (self.draw_id)
                file_name = get_resource_filename(resource_name, 'html')
                html_file.write('<div class="constant-buffer">\n')
                html_file.write('<h4>📊 常量缓冲区</h4>\n')
                html_file.write('<a href="%s">%s</a>\n' % (file_name, resource_name))
                html_file.write('</div>\n')

        html_file.write('</div>\n')
        html_file.write('</div>\n')

        if not self.isDispatch():
            # color buffer section
            if config['WRITE_COLOR_BUFFER']:
                for idx, resource_id in enumerate(self.color_buffers):
                    if not resource_id or resource_id == rd.ResourceId.Null():
                        continue
                    resource_name = get_resource_name(controller, resource_id)
                    # TODO: ugly
                    file_name = get_resource_filename('%s--%04d_c%d' % (resource_name, self.draw_id, idx), IMG_EXT)
                    self.writeTextureHtml(html_file, controller, 'c%d: %s' % (idx, resource_name), resource_id, file_name)

            # depth buffer section
            if config['WRITE_DEPTH_BUFFER']:
                if self.depth_buffer != rd.ResourceId.Null():
                    resource_id = self.depth_buffer
                    resource_name = get_resource_name(controller, resource_id)
                    # TODO: ugly again
                    file_name = get_resource_filename('%s--%04d_z' % (resource_name, self.draw_id), IMG_EXT)
                    self.writeTextureHtml(html_file, controller, 'z: %s' % (resource_name), resource_id, file_name)

            # texture section
            if not self.isClear() and not self.isCopy() and config['WRITE_TEXTURE']:
                html_file.write('<div class="texture-section">\n')
                html_file.write('<h4>🖼️ 贴图资源</h4>\n')
                for idx, resource_id in enumerate(self.textures):
                    if not resource_id or resource_id == rd.ResourceId.Null():
                        continue
                    resource_name = get_resource_name(controller, resource_id)
                    file_name = get_resource_filename(resource_name, IMG_EXT)
                    self.writeTextureHtml(html_file, controller, 't%s: %s' % (idx, resource_name), resource_id, file_name)
                html_file.write('</div>\n')
        # TODO: add UAV / image etc

    def exportResources(self, controller):
        if not config['WRITE_COLOR_BUFFER'] and not config['WRITE_DEPTH_BUFFER'] and not config['WRITE_TEXTURE']:
            return

        if API_TYPE == rd.GraphicsAPI.Vulkan and self.isDispatch():
            # on Android devices, Vulkan dispatch calls will likely crash renderdoc, so we skip them
            return

        if config['WRITE_COLOR_BUFFER'] or config['WRITE_DEPTH_BUFFER']:
            controller.SetFrameEvent(self.event_id, False)

        # WRITE textures
        if config['WRITE_TEXTURE']:
            for idx, resource_id in enumerate(self.textures):
                if resource_id == rd.ResourceId.Null():
                    continue
                resource_name = get_resource_name(controller, resource_id)
                file_name = get_resource_filename(resource_name, IMG_EXT)
                export_texture(controller, resource_id, file_name)

        # WRITE render targtes (aka outputs)
        if config['WRITE_COLOR_BUFFER']:
            for idx, resource_id in enumerate(self.color_buffers):
                if resource_id != rd.ResourceId.Null():
                    resource_name = get_resource_name(controller, resource_id)
                    file_name = get_resource_filename('%s--%04d_c%d' % (resource_name, self.draw_id, idx), IMG_EXT)
                    if config['WRITE_COLOR_BUFFER']:
                        export_texture(controller, resource_id, file_name)

        # depth
        if config['WRITE_DEPTH_BUFFER'] and self.depth_buffer:
            resource_id = self.depth_buffer
            if resource_id != rd.ResourceId.Null():
                resource_name = get_resource_name(controller, resource_id)
                file_name = get_resource_filename('%s--%04d_z' % (resource_name, self.draw_id), IMG_EXT)
                if not Path(file_name).exists():
                    export_texture(controller, resource_id, file_name)

    draw_id = None
    draw_desc = None # struct ActionDescription
    shader_names = None
    state_key = None
    color_buffers = None
    depth_buffer = None

def export_texture(controller, resource_id, file_name):
    global g_assets_folder

    file_path = g_assets_folder / file_name
    if file_path.exists():
        return

    file_name = str(file_path)
    texture_info = get_texture_info(controller, resource_id)
    if not texture_info:
        return

    # 图片压缩和尺寸控制配置
    MAX_IMAGE_SIZE = config.get('MAX_IMAGE_SIZE', 512)  # 最大图片尺寸
    JPEG_QUALITY = config.get('JPEG_QUALITY', 85)       # JPEG压缩质量 (0-100)

    texsave = rd.TextureSave()
    fmt = rd.ResourceFormat(texture_info.format).Name()
    if texture_info.format.compCount == 3 or texture_info.format.compCount == 1 or 'A2' in fmt or 'A16' in fmt:
        texsave.alpha = rd.AlphaMapping.Discard
    else:
        texsave.alpha = rd.AlphaMapping.BlendToCheckerboard
    texsave.destType = rd.FileType.JPG
    texsave.mip = 0
    texsave.slice.sliceIndex = 0
    texsave.resourceId = resource_id

    print("Writing %s" % file_name)
    controller.SaveTexture(texsave, file_name)

    # 图片压缩和尺寸优化
    if config.get('IMAGE_COMPRESSION', True):
        try:
            from PIL import Image
            import os
            
            # 打开图片
            img = Image.open(file_name)
            
            # 获取原始尺寸
            original_width, original_height = img.size
            
            # 计算缩放比例
            scale = min(MAX_IMAGE_SIZE / original_width, MAX_IMAGE_SIZE / original_height, 1.0)
            
            if scale < 1.0:
                # 计算新尺寸
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                
                # 使用高质量的缩放算法
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
            
            # 保存压缩后的图片
            img.save(file_name, 'JPEG', quality=JPEG_QUALITY, optimize=True)
            
            # 获取文件大小
            file_size = os.path.getsize(file_name)
            file_size_kb = file_size / 1024
            print(f"Compressed image: {file_size_kb:.1f} KB")
            
        except ImportError:
            print("PIL not available, skipping image compression")
        except Exception as e:
            print(f"Image compression failed: {e}")

    if not 'pyrenderdoc' in globals() and texture_info.creationFlags & rd.TextureCategory.DepthTarget:
        # equalizeHist
        try:
            import cv2
            import numpy as np
        except ImportError as error:
            return

        z_rgb = cv2.imread(file_name)
        z_r = z_rgb[:, :, 2]
        equ = cv2.equalizeHist(z_r)
        # res = np.hstack((z_r,equ)) #stacking images side-by-side
        cv2.imwrite(file_name, equ)

def pretty_number(num):
    """统一数字格式化，使用K/M/G单位（1000进制）"""
    if num < 1e3:
        return str(num)
    if num < 1e6:
        return "%.1fK" % (num/1e3) + " (千)"
    if num < 1e9:
        return "%.1fM" % (num/1e6) + " (百万)"
    if num < 1e12:
        return "%.1fG" % (num/1e9) + " (十亿)"
    return "%.1fT" % (num/1e12) + " (万亿)"

def format_memory_size(bytes_size):
    """统一内存大小格式化，使用KB/MB/GB单位（1024进制）"""
    if bytes_size == 0:
        return "0 MB"
    if bytes_size < 1024:
        return "%.1f B" % bytes_size
    elif bytes_size < 1024 * 1024:
        return "%.1f KB" % (bytes_size / 1024)
    elif bytes_size < 1024 * 1024 * 1024:
        return "%.1f MB" % (bytes_size / (1024 * 1024))
    else:
        return "%.1f GB" % (bytes_size / (1024 * 1024 * 1024))

def format_time_duration(microseconds):
    """统一时间格式化，使用微秒/毫秒/秒单位"""
    if microseconds < 1000:
        return "%.2f μs" % microseconds + " (微秒)"
    elif microseconds < 1000000:
        return "%.2f ms" % (microseconds / 1000) + " (毫秒)"
    else:
        return "%.2f s" % (microseconds / 1000000) + " (秒)"

def format_size_range(max_size, min_size):
    """统一尺寸范围格式化，添加像素单位"""
    if max_size == 0:
        return "无数据"
    if min_size == float('inf'):
        return "%d px" % max_size
    if max_size == min_size:
        return "%d px" % max_size
    return "%d~%d px" % (max_size, min_size)

class Frame:
    #
    def __init__(self):
        self.passes = []
        self.textures = set()
        self.shaders = OrderedDict()

        self.addPass()
        self.stateNameDict = defaultdict(int)

    def addPass(self):
        # print("addPass %d" % (len(self.passes)))
        State.current = State.default

        self.passes.append(Pass())
        Pass.current = self.passes[-1]

    def getImageLinkOrNothing(self, filename, width='100%'):
        if not filename:
            return ''

        return '<img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjVmNWY1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPlByZXZpZXc8L3RleHQ+PC9zdmc=" data-src="%s" alt="Preview" class="lazyload" loading="lazy" style="max-width: %s; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 5px; transition: transform 0.3s ease;">' % (filename, width)

    def writeShaderOverview(self, html_file, controller):
        # 着色器概览已取消
        pass

    def writeResourceOverview(self, html_file, controller):

        if API_TYPE != rd.GraphicsAPI.OpenGL:
            # TODO: support APIs besides OpenGL
            return

        if not g_frame.textures:
            return

        texture_tips = []

        for resource_id in g_frame.textures:
            if not resource_id or resource_id == rd.ResourceId.Null():
                continue
            texture_tips.append(TextureTip(controller, resource_id))

        def getName(elem):
            return elem.name

        def getTipsLength(elem):
            return len(elem.tips)

        texture_tips = sorted(texture_tips, key=getName)
        texture_tips = sorted(texture_tips, key=getTipsLength, reverse=True)

        html_file.write('<div class="card">\n')
        html_file.write('<div class="card-header">📦 资源概览</div>\n')
        html_file.write('<div class="card-content">\n')
        html_file.write('<table>\n')
        html_file.write('<thead>\n')
        html_file.write('<tr><th>名称</th><th>类型</th><th>用途</th><th>尺寸</th><th>Mip</th><th>格式</th><th>字节</th><th>提示</th><th>预览</th></tr>\n')
        html_file.write('</thead>\n')
        html_file.write('<tbody>\n')

        for tip in texture_tips:
            file_name = get_resource_filename(get_resource_name(controller, tip.resource_id), IMG_EXT)
            tex_info = tip.info
            if config['WRITE_TEXTURE']:
                export_texture(controller, tex_info.resourceId, file_name)
            texType = '%s' % rd.TextureType(tex_info.type)
            texType = texType.replace('TextureType.', '')
            # 翻译贴图类型为中文
            texType = texType.replace('Texture2D', '2D贴图')
            texType = texType.replace('Texture3D', '3D贴图')
            texType = texType.replace('TextureCube', '立方体贴图')
            texType = texType.replace('Texture1D', '1D贴图')
            texType = texType.replace('Texture1DArray', '1D贴图数组')
            texType = texType.replace('Texture2DArray', '2D贴图数组')
            texType = texType.replace('TextureCubeArray', '立方体贴图数组')
            texType = texType.replace('Texture3DArray', '3D贴图数组')
            usages = '%s' % rd.TextureCategory(tex_info.creationFlags)
            usages = usages.replace('TextureCategory.', '').replace('ShaderRead','T').replace('ColorTarget','C').replace('DepthTarget','Z').replace('|',''),
            html_file.write('<tr>\n')
            html_file.write('<td>%s</td>\n' % tip.name)
            html_file.write('<td>%s</td>\n' % texType)
            html_file.write('<td>%s</td>\n' % '|'.join(usages))
            html_file.write('<td>%s</td>\n' % '%dx%d' % (tex_info.width, tex_info.height))
            html_file.write('<td>%d</td>\n' % tex_info.mips)
            html_file.write('<td>%s</td>\n' % tip.format)
            html_file.write('<td>%s</td>\n' % pretty_number(tex_info.byteSize))
            html_file.write('<td>%s</td>\n' % '<br>'.join(tip.tips))
            html_file.write('<td><img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9Ijc1IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNmNWY1ZjUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+UmVzb3VyY2U8L3RleHQ+PC9zdmc=" data-src="%s" alt="Preview" class="lazyload" loading="lazy" style="max-width: 100px; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 2px; transition: transform 0.3s ease;"></td>\n' % file_name)
            html_file.write('</tr>\n')

        html_file.write('</tbody>\n')
        html_file.write('</table>\n')
        html_file.write('</div>\n')
        html_file.write('</div>\n')

    def writeFrameOverview(self, html_file, controller):
        summary_csv = open(g_assets_folder / 'summary.csv',"w") 

        html_file.write('<div class="card">\n')
        html_file.write('<div class="card-header">📊 渲染资产统计</div>\n')
        html_file.write('<div class="card-content">\n')

        # 初始化所有统计变量，确保在任何情况下都有定义
        total_textures = 0
        total_texture_size = 0
        total_max_size = 0
        total_min_size = float('inf')
        
        total_draws = 0
        total_vertices = 0
        total_polygons_accurate = 0
        total_time = 0
        
        # 初始化其他变量
        largest_texture_info = None
        largest_texture_id = None
        smallest_texture_info = None
        smallest_texture_id = None
        smallest_name = ""
        smallest_format = ""
        smallest_memory = 0
        smallest_found = False

        texture_formats = []
        texture_types = []
        mipmap_counts = []
        size_analysis = []  # 初始化size_analysis变量
        
        # 分析贴图资源 - 只从Color Pass中收集贴图
        all_textures = set()
        
        # 从所有Pass中收集贴图资源
        print(f"Debug: 开始收集贴图，总Pass数: {len(self.passes)}")
        for p in self.passes:
            for s in p.states:
                for d in s.draws:
                    # 收集所有Pass中的所有贴图
                    print(f"Debug: 处理绘制调用 {d.draw_id}: {d.name}")
                    print(f"Debug: 该绘制的贴图数量: {len(d.textures)}")
                    for resource_id in d.textures:
                        if resource_id != rd.ResourceId.Null():
                            # 获取贴图信息
                            texture_info = get_texture_info(controller, resource_id)
                            if texture_info:
                                # 收集所有贴图，不做任何过滤
                                all_textures.add(resource_id)
                                print(f"Debug: 从绘制调用收集贴图: {resource_id}")
                            else:
                                print(f"Debug: 贴图信息获取失败: {resource_id}")
                        else:
                            print(f"Debug: 跳过空贴图ID")
        
        print(f"Debug: 从Pass收集到的贴图数量: {len(all_textures)}")
        
        # 如果从Pass中没有收集到贴图，直接从RenderDoc API获取所有贴图
        if len(all_textures) == 0:
            try:
                # 直接从RenderDoc API获取所有贴图
                textures = controller.GetTextures()
                for texture in textures:
                    if texture.resourceId != rd.ResourceId.Null():
                        all_textures.add(texture.resourceId)
            except Exception as e:
                pass
        
        # 如果还是没有贴图，尝试从所有资源中获取
        if len(all_textures) == 0:
            try:
                # 从所有资源中获取贴图
                resources = controller.GetResources()
                for resource in resources:
                    if resource.resourceId != rd.ResourceId.Null():
                        # 检查是否为贴图资源
                        texture_info = get_texture_info(controller, resource.resourceId)
                        if texture_info:
                            all_textures.add(resource.resourceId)
                            print(f"Debug: 从资源获取贴图: {resource.resourceId} - {resource.name}")
            except Exception as e:
                print(f"Debug: 从资源获取贴图失败: {e}")
        

        

        
        # 分析收集到的贴图 - 所有数据来自RenderDoc texture_info
        # 重新初始化最大和最小贴图变量
        largest_texture_info = None  # 记录最大贴图的信息
        largest_texture_id = None
        smallest_texture_info = None
        smallest_texture_id = None
        smallest_name = ""
        smallest_format = ""
        smallest_memory = 0
        smallest_found = False
        
        print(f"Debug: 开始分析 {len(all_textures)} 个贴图")
        for resource_id in all_textures:
            texture_info = get_texture_info(controller, resource_id)
            if not texture_info:
                print(f"Debug: 贴图信息获取失败: {resource_id}")
                continue

            # 统计所有贴图数据，不做任何过滤
            texture_memory = texture_info.width * texture_info.height * 4  # 假设RGBA格式
            max_size = max(texture_info.width, texture_info.height)
            min_size = min(texture_info.width, texture_info.height)
            
            total_textures += 1
            total_texture_size += texture_memory
            
            # 收集贴图格式信息 - 只保留主要格式
            texture_format = rd.ResourceFormat(texture_info.format).Name()
            
            # 过滤掉不需要的格式
            skip_formats = [
                'BC7_SRGB', 'BC7_UNORM', 'BC6_UFLOAT', 'BC5_UNORM', 'BC1_UNORM',
                'R16G16_FLOAT', 'R16_FLOAT', 'R10G10B10A2_UNORM', 'R32_FLOAT',
                'R8G8B8A8_UNORM', 'R8G8B8A8_SRGB', 'R16G16B16A16_FLOAT',
                'R16G16_UNORM', 'A8_UNORM', 'R32_TYPELESS', 'D32S8_TYPELESS',
                'R11G11B10_FLOAT', 'R8_UNORM', 'R16_TYPELESS', 'R16_UNORM',
                'R8G8_UNORM', 'R32G32B32A32_FLOAT'
            ]
            
            if texture_format not in skip_formats:
                texture_formats.append(texture_format)
            
            # 收集贴图类型信息
            if hasattr(texture_info, 'type'):
                texture_type = str(texture_info.type)
                texture_types.append(texture_type)
            
            # 收集Mipmap信息
            if hasattr(texture_info, 'mips'):
                mipmap_counts.append(texture_info.mips)
            

            
            # 追踪最大尺寸的贴图
            if max_size > total_max_size:
                total_max_size = max_size
                largest_texture_info = texture_info
                largest_texture_id = resource_id
            
            total_min_size = min(total_min_size, min_size)
        
        print(f"Debug: 贴图分析完成，总贴图数: {total_textures}")
        

        
        # 直接使用RenderDoc提供的准确数据
        total_instances = 0
        
        for p in self.passes:
            for s in p.states:
                for d in s.draws:
                    total_draws += 1
                    
                    # 尝试多种方式收集几何体数据
                    if hasattr(d, 'draw_desc') and d.draw_desc:
                        # 方法1: 从 draw_desc 收集顶点数
                        if hasattr(d.draw_desc, 'numVertices') and d.draw_desc.numVertices > 0:
                            total_vertices += d.draw_desc.numVertices
                        
                        # 方法2: 从 draw_desc 的其他可能字段收集顶点数
                        if hasattr(d.draw_desc, 'vertexCount') and d.draw_desc.vertexCount > 0:
                            total_vertices += d.draw_desc.vertexCount
                        
                        # 方法3: 从绘制调用的其他属性收集顶点数
                        if hasattr(d, 'vertexCount') and d.vertexCount > 0:
                            total_vertices += d.vertexCount
                        
                        # 方法4: 从绘制调用的其他可能属性收集顶点数
                        if hasattr(d, 'numVertices') and d.numVertices > 0:
                            total_vertices += d.numVertices
                        
                        # 根据图元类型计算面数
                        if hasattr(d.draw_desc, 'topology'):
                            topology = str(d.draw_desc.topology)
                            if hasattr(d.draw_desc, 'numVertices') and d.draw_desc.numVertices > 0:
                                vertices = d.draw_desc.numVertices
                                if 'Triangle' in topology:
                                    total_polygons_accurate += vertices // 3
                                elif 'Quad' in topology:
                                    total_polygons_accurate += vertices // 4
                                elif 'Line' in topology:
                                    total_polygons_accurate += vertices // 2
                                else:
                                    # 默认按三角形计算
                                    total_polygons_accurate += vertices // 3
                    
                    # 收集GPU时间 - 来自RenderDoc gpu_duration
                    if hasattr(d, 'gpu_duration'):
                        total_time += d.gpu_duration
        

        
        # 处理最小尺寸的显示
        # 使用全局的format_size_range函数
        
        # 处理内存显示
        # 使用全局的format_memory_size函数
        
        # 添加表格样式
        html_file.write('<style>\n')
        html_file.write('.stats-table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }\n')
        html_file.write('.stats-table th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; text-align: left; font-weight: 600; }\n')
        html_file.write('.stats-table td { padding: 12px 15px; border-bottom: 1px solid #eee; }\n')
        html_file.write('.stats-table tr:hover { background-color: #f8f9fa; }\n')
        html_file.write('.stats-table .highlight { background-color: #e3f2fd; font-weight: 600; }\n')
        html_file.write('.summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }\n')
        html_file.write('.summary-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }\n')
        html_file.write('.summary-card .value { font-size: 24px; font-weight: bold; color: #667eea; }\n')
        html_file.write('.summary-card .label { color: #666; margin-top: 5px; }\n')
        html_file.write('</style>\n')
        
        # 统一统计表格
        html_file.write('<table class="stats-table">\n')
        html_file.write('<thead>\n')
        html_file.write('<tr>\n')
        html_file.write('<th>类别</th>\n')
        html_file.write('<th>项目</th>\n')
        html_file.write('<th>数值</th>\n')
        html_file.write('</tr>\n')
        html_file.write('</thead>\n')
        html_file.write('<tbody>\n')
        

            
                    # 添加最大贴图的详细信息
        if largest_texture_info and largest_texture_id:
            largest_name = get_resource_name(controller, largest_texture_id)
            largest_format = rd.ResourceFormat(largest_texture_info.format).Name()
            largest_memory = largest_texture_info.width * largest_texture_info.height * 4
            
                    
            
            for resource_id in all_textures:
                texture_info = get_texture_info(controller, resource_id)
                if not texture_info:
                    continue
                # 检查是否为渲染目标，如果是则跳过
                texture_format = rd.ResourceFormat(texture_info.format).Name()
                # 跳过深度/模板缓冲区和渲染目标
                if 'Depth' in texture_format or 'Stencil' in texture_format:
                    continue  # 跳过深度/模板缓冲区
                # 检查是否为渲染目标（通常有特定的命名模式）
                resource_name = get_resource_name(controller, resource_id)
                if resource_name and ('Target' in resource_name or 'Render' in resource_name):
                    continue  # 跳过渲染目标
                
                max_size = max(texture_info.width, texture_info.height)
                if not smallest_found or max_size < min(smallest_texture_info.width, smallest_texture_info.height):
                    smallest_texture_info = texture_info
                    smallest_texture_id = resource_id
                    smallest_name = get_resource_name(controller, resource_id)
                    smallest_format = texture_format
                    smallest_memory = texture_info.width * texture_info.height * 4
                    smallest_found = True
            


            # 只跳过明显的深度/模板缓冲区
            if 'Depth' not in largest_format and 'Stencil' not in largest_format:
                # 简化使用位置显示，最多显示前5个
                usage_passes = []
                for p in self.passes:
                    for s in p.states:
                        for d in s.draws:
                            if hasattr(d, 'textures') and largest_texture_id in d.textures:
                                usage_passes.append(f"Pass {len(usage_passes)+1}")
                            if hasattr(d, 'color_buffers') and largest_texture_id in d.color_buffers:
                                usage_passes.append(f"Pass {len(usage_passes)+1} (颜色缓冲区)")
                            # 跳过深度缓冲区
                            if hasattr(d, 'depth_buffer') and d.depth_buffer == largest_texture_id:
                                continue
                            
                            # 最多显示5个使用位置
                            if len(usage_passes) >= 5:
                                break
                        if len(usage_passes) >= 5:
                            break
                    if len(usage_passes) >= 5:
                        break
                
                if len(usage_passes) > 5:
                    usage_info = f"使用位置: {', '.join(usage_passes[:5])}... (共{len(usage_passes)}个)"
                else:
                    usage_info = f"使用位置: {', '.join(usage_passes)}" if usage_passes else "使用位置: 未找到"
                
                html_file.write('<tr class="highlight">\n')
                html_file.write('<td colspan="3" style="text-align: center; font-style: italic; color: #666;">🔍 最大贴图详情：' + largest_name + f' ({largest_texture_info.width}×{largest_texture_info.height}, {largest_format}, {format_memory_size(largest_memory)}) - {usage_info}</td>\n')
                html_file.write('</tr>\n')
                
                # 添加最小贴图信息
                if smallest_found and smallest_texture_info and smallest_texture_id:
                    html_file.write('<tr class="highlight">\n')
                    html_file.write('<td colspan="3" style="text-align: center; font-style: italic; color: #666;">🔍 最小贴图详情：' + smallest_name + f' ({smallest_texture_info.width}×{smallest_texture_info.height}, {smallest_format}, {format_memory_size(smallest_memory)})</td>\n')
                    html_file.write('</tr>\n')
                

        
        # 确保变量有合理的默认值
        if total_polygons_accurate < 0:
            total_polygons_accurate = 0
        
        # 如果所有方法都失败，使用估算
        if total_vertices == 0 and total_draws > 0:
            # 如果连顶点数都没有，按绘制调用数估算
            total_vertices = total_draws * 1000  # 每个绘制调用假设1000个顶点
            total_polygons_accurate = total_draws * 333  # 每个绘制调用假设333个面
        
        model_stats = [
            {'category': '🎯 模型', 'item': '总绘制调用', 'value': str(total_draws) + " 次"},
            {'category': '🎯 模型', 'item': '总顶点数', 'value': pretty_number(total_vertices)},
            {'category': '🎯 模型', 'item': '总面数', 'value': pretty_number(total_polygons_accurate)},
        ]
        

        
        # 贴图统计
        texture_stats = [
            {'category': '🖼️ 贴图', 'item': '总贴图数', 'value': str(total_textures) + " 个"},
            {'category': '🖼️ 贴图', 'item': '总内存', 'value': format_memory_size(total_texture_size)},
            {'category': '🖼️ 贴图', 'item': '尺寸范围', 'value': format_size_range(total_max_size, total_min_size)},
        ]
        

        
        # 添加贴图类型统计
        if texture_types:
            type_stats = {}
            for type_name in texture_types:
                if type_name in type_stats:
                    type_stats[type_name] += 1
                else:
                    type_stats[type_name] = 1
            
            for type_name, count in type_stats.items():
                # 翻译贴图类型为中文
                translated_type = type_name
                translated_type = translated_type.replace('TextureType.', '')
                translated_type = translated_type.replace('Texture2D', '2D贴图')
                translated_type = translated_type.replace('Texture3D', '3D贴图')
                translated_type = translated_type.replace('TextureCube', '立方体贴图')
                translated_type = translated_type.replace('Texture1D', '1D贴图')
                translated_type = translated_type.replace('Texture1DArray', '1D贴图数组')
                translated_type = translated_type.replace('Texture2DArray', '2D贴图数组')
                translated_type = translated_type.replace('TextureCubeArray', '立方体贴图数组')
                translated_type = translated_type.replace('Texture3DArray', '3D贴图数组')
                
                texture_stats.append({
                    'category': '🖼️ 贴图', 
                    'item': f' {translated_type}', 
                    'value': f"{count} 个"
                })
        

        
        # 添加最大贴图的统计信息（排除深度缓冲区）
        if largest_texture_info and largest_texture_id:
            largest_name = get_resource_name(controller, largest_texture_id)
            largest_format = rd.ResourceFormat(largest_texture_info.format).Name()
            
            # 只跳过明显的深度/模板缓冲区
            if 'Depth' not in largest_format and 'Stencil' not in largest_format:
                texture_stats.append({
                    'category': '🖼️ 贴图', 
                    'item': '最大贴图', 
                    'value': f"{largest_name} ({largest_texture_info.width}×{largest_texture_info.height})"
                })
            else:
                texture_stats.append({
                    'category': '🖼️ 贴图', 
                    'item': '最大贴图', 
                    'value': "深度缓冲区 (已排除)"
                })
        
        # 添加最小贴图的统计信息（排除渲染目标）
        if smallest_found and smallest_texture_info and smallest_texture_id:
            smallest_name = get_resource_name(controller, smallest_texture_id)
            smallest_format = rd.ResourceFormat(smallest_texture_info.format).Name()
            
            # 只跳过明显的深度/模板缓冲区
            if 'Depth' not in smallest_format and 'Stencil' not in smallest_format:
                texture_stats.append({
                    'category': '🖼️ 贴图', 
                    'item': '最小贴图', 
                    'value': f"{smallest_name} ({smallest_texture_info.width}×{smallest_texture_info.height})"
                })
            else:
                texture_stats.append({
                    'category': '🖼️ 贴图', 
                    'item': '最小贴图', 
                    'value': "深度缓冲区 (已排除)"
                })
        

        
        # 确保所有变量都有合理的默认值
        if not largest_texture_info:
            largest_texture_info = None
        if not largest_texture_id:
            largest_texture_id = None
        
        # 添加详细的尺寸分析说明
        if total_max_size > 0:
            if total_max_size >= 4096:
                size_analysis.append("包含高分辨率贴图 (≥4K)")
            if total_min_size <= 64:
                size_analysis.append("包含小尺寸贴图 (≤64px)")
            if total_max_size == total_min_size:
                size_analysis.append("所有贴图尺寸一致")
            else:
                size_analysis.append("贴图尺寸多样化")
            
            # 分析最大贴图的详细信息（排除深度缓冲区）
            if largest_texture_info and largest_texture_id:
                largest_name = get_resource_name(controller, largest_texture_id)
                largest_format = rd.ResourceFormat(largest_texture_info.format).Name()
                
                # 只跳过明显的深度/模板缓冲区
                if 'Depth' not in largest_format and 'Stencil' not in largest_format:
                    size_analysis.append(f"最大贴图: {largest_name} ({largest_texture_info.width}×{largest_texture_info.height}, {largest_format})")
                    
                    # 特殊尺寸分析
                    if total_max_size == 5120:
                        size_analysis.append("→ 5120×5120 (可能是5K纹理或特殊渲染目标)")
                    elif total_max_size > 4096:
                        size_analysis.append(f"→ {total_max_size}×{total_max_size} (超高分辨率)")
                    elif total_max_size >= 2048:
                        size_analysis.append(f"→ {total_max_size}×{total_max_size} (高分辨率)")
                    
                    # 添加最小贴图分析
                    if smallest_found and smallest_texture_info and smallest_texture_id:
                        smallest_name = get_resource_name(controller, smallest_texture_id)
                        smallest_format = rd.ResourceFormat(smallest_texture_info.format).Name()
                        if 'Depth' not in smallest_format and 'Stencil' not in smallest_format:
                            size_analysis.append(f"最小贴图: {smallest_name} ({smallest_texture_info.width}×{smallest_texture_info.height}, {smallest_format})")
                else:
                    size_analysis.append("最大贴图: 深度缓冲区 (已排除)")
        else:
            size_analysis.append("无贴图数据")
        
        # 收集RenderDoc API的详细信息
        renderdoc_api_info = {
            'draw_calls': {
                'total': total_draws,
                'types': {},  # 暂时为空字典
                'primitives': {}  # 暂时为空字典
            },
            'geometry': {
                'vertices': total_vertices,
                'instances': total_instances,
                'polygons': total_polygons_accurate
            },
            'textures': {
                'count': total_textures,
                'memory': total_texture_size,
                'size_range': f"{total_min_size}~{total_max_size}",
                'largest': largest_texture_info
            },
            'performance': {
                'gpu_time': total_time,
                'passes': len(self.passes)
            }
        }
        
        # 计算性能评级
        if total_polygons_accurate > 1000000:
            complexity_rating = "高"
        elif total_polygons_accurate > 500000:
            complexity_rating = "中"
        else:
            complexity_rating = "低"
        
        # 性能统计
        performance_stats = [
            {'category': '⚡ 性能', 'item': '总绘制调用', 'value': str(total_draws) + " 次"},
            {'category': '⚡ 性能', 'item': '总渲染时间', 'value': format_time_duration(total_time * 1000)},  # 转换为微秒
            {'category': '⚡ 性能', 'item': '渲染Pass数', 'value': str(len(self.passes)) + " 个"},
        ]
        
        # 输出所有统计数据，合并同类别单元格
        all_stats = model_stats + texture_stats + performance_stats
        current_category = None
        category_counts = {}
        
        # 计算每个类别的行数
        for stat in all_stats:
            category = stat['category']
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        # 输出表格行
        for i, stat in enumerate(all_stats):
            html_file.write('<tr>\n')
            
            # 如果是新类别的第一行，输出带rowspan的类别单元格
            if stat['category'] != current_category:
                current_category = stat['category']
                rowspan = category_counts[current_category]
                html_file.write('<td rowspan="%d" style="vertical-align: middle; background-color: #f8f9fa; font-weight: bold;">%s</td>\n' % (rowspan, stat['category']))
            
            html_file.write('<td>%s</td>\n' % stat['item'])
            html_file.write('<td><strong>%s</strong></td>\n' % stat['value'])
            html_file.write('</tr>\n')
        
        html_file.write('</tbody>\n')
        html_file.write('</table>\n')
        
        html_file.write('</div>\n')
        html_file.write('</div>\n')

    def writeBindStats(self, html_file, label, item):
        # TODO: add redundants
        html_file.write('<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>\n' % (label, item.calls, item.sets, item.nulls))

    def getUniqueStateName(self, passName, stateName):
        if self.stateNameDict[stateName] == 1:
            return stateName
        return '%s_%s' % (passName, stateName)

    def writeDAG(self, controller=None):
        filename = g_assets_folder / 'dag.html' # TODO: ugly
        markdown = open(filename, 'w', encoding='utf-8')
        markdown.write(mermaid_head)
        markdown.write('<div class="mermaid">\n')
        markdown.write('flowchart LR\n')
        pass_count = len(self.passes)

        # subgraph
        for i in range(0, pass_count):
            p = self.passes[i]
            pass_name = p.getName(controller) if controller else f"Pass{i}"
            markdown.write('subgraph %s\n' % pass_name)

            if True:
                # set sort
                states = list(p.stateNames)
                state_count = len(states)
                if state_count == 1:
                    # no siblings
                    markdown.write('%s\n' % (self.getUniqueStateName(pass_name, states[0])))
                else:
                    for j in range(0, state_count - 1):
                        markdown.write('%s --> %s\n' % (self.getUniqueStateName(pass_name, states[j]), self.getUniqueStateName(pass_name, states[j+1])))
            else:
                state_count = len(p.states)
                if state_count == 1:
                    # no siblings
                    markdown.write('%s\n' % (p.states[0].getUniqueName()))
                else:
                    for j in range(0, state_count - 1):
                        markdown.write('%s --> %s\n' % (p.states[j].getUniqueName(), p.states[j+1].getUniqueName()))

            markdown.write('end\n')

            if i < pass_count - 1:
                # connect neighboring passes, only valid in "flowchart"
                next = self.passes[i+1]
                next_name = next.getName(controller) if controller else f"Pass{i+1}"
                markdown.write('%s -.-> %s\n' % (pass_name, next_name))
        markdown.writelines('</div>\n\n')

        # linear order
        dag = set()
        # markdown.write('<h1>PSO diagram</h1>\n')
        # markdown.write('<div class="mermaid">\n')
        # markdown.write('graph LR\n')

        # state_count = len(g_states)

        # for i in range(1, state_count):
        #     src = g_states[i]
        #     markdown.write('%s ==> %s\n' % (g_states[i-1].name, g_states[i].name))
        #     for c in src.getFirstDraw().color_buffers:
        #         if c == rd.ResourceId.Null():
        #             continue
        #         for j in range(i+1, state_count):
        #             dst = g_states[j]
        #             for t in dst.getFirstDraw().textures:
        #                 if t == rd.ResourceId.Null():
        #                     continue
        #                 if c == t:
        #                     # src.c becomes dst.t
        #                     dag.add((src, dst, get_resource_name(controller, c)))

        # # TODO: merge linear sort and topology sort
        # for src, dst, c in dag:
        #     markdown.write('%s -.->|%s| %s\n' % (src.name, c, dst.name))

        # markdown.writelines('</div>\n\n')

        markdown.close()

    def writeAPIOverview(self, html_file, controller):
        info = controller.GetFrameInfo()
        stats = info.stats
        if not stats.recorded:
            return

        html_file.write('<div class="api-overview">\n')
        html_file.write('<h2>📊 API 概览</h2>\n')
        
        html_file.write('<div class="stats-section">\n')
        html_file.write('<h3>🎯 绘制调用统计</h3>\n')
        html_file.write('<table class="stats-table">\n')
        html_file.write('<thead>\n')
        html_file.write('<tr><th>类型</th><th>调用次数</th><th>实例化</th><th>间接</th></tr>\n')
        html_file.write('</thead>\n')
        html_file.write('<tbody>\n')
        html_file.write('<tr><td>绘制</td><td>%d</td><td>%d</td><td>%d</td></tr>\n' % (stats.draws.calls, stats.draws.instanced, stats.draws.indirect))
        html_file.write('<tr><td>分发</td><td>%d</td><td>0</td><td>%d</td></tr>\n' % (stats.dispatches.calls, stats.dispatches.indirect))
        html_file.write('</tbody>\n')
        html_file.write('</table>\n')
        html_file.write('</div>\n')
        
        html_file.write('<div class="stats-section">\n')
        html_file.write('<h3>📦 资源更新统计</h3>\n')
        html_file.write('<table class="stats-table">\n')
        html_file.write('<thead>\n')
        html_file.write('<tr><th>调用次数</th><th>客户端写入</th><th>服务器写入</th></tr>\n')
        html_file.write('</thead>\n')
        html_file.write('<tbody>\n')
        html_file.write('<tr><td>%d</td><td>%d</td><td>%d</td></tr>\n' % (stats.updates.calls, stats.updates.clients, stats.updates.servers))
        html_file.write('</tbody>\n')
        html_file.write('</table>\n')
        html_file.write('</div>\n')
        
        html_file.write('<div class="stats-section">\n')
        html_file.write('<h3>🔗 资源绑定统计</h3>\n')
        html_file.write('<table class="stats-table">\n')
        html_file.write('<thead>\n')
        html_file.write('<tr><th>类型</th><th>调用次数</th><th>设置</th><th>空值</th></tr>\n')
        html_file.write('</thead>\n')
        html_file.write('<tbody>\n')
        self.writeBindStats(html_file, '索引缓冲区绑定', stats.indices)
        self.writeBindStats(html_file, '顶点缓冲区绑定', stats.vertices)
        self.writeBindStats(html_file, '顶点布局绑定', stats.layouts)
        self.writeBindStats(html_file, '混合状态绑定', stats.blends)
        self.writeBindStats(html_file, '深度模板状态绑定', stats.depths)
        self.writeBindStats(html_file, '光栅化状态绑定', stats.rasters)
        self.writeBindStats(html_file, '输出合并和UAV绑定', stats.outputs)
        html_file.write('</tbody>\n')
        html_file.write('</table>\n')
        html_file.write('</div>\n')
        html_file.write('</div>\n')

    def writeIndexHtml(self, html_file, controller):

        pipelineTypes = [
                "D3D11",
                "D3D12",
                "OpenGL",
                "Vulkan",
        ]
        GPUVendors = [
            "Unknown",
            "ARM",
            "AMD",
            "Broadcom",
            "Imagination",
            "Intel",
            "nVidia",
            "Qualcomm",
            "Verisilicon",
            "Software",
        ]

        api_prop = controller.GetAPIProperties()

        # Header
        if config['MINIMALIST']:
            html_file.write(html_minimalist_head)
        else:
            html_file.write(html_head)
        html_file.write('<div style="display: flex; align-items: center; margin-bottom: 20px; background: linear-gradient(135deg, #ff6600, #ff8533); padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(255,102,0,0.2);">\n')
        # 复制logo文件到输出目录
        # 使用assets文件夹中的logo文件
        html_file.write('<img src="assets/logo.png" alt="Logo" style="height: 50px; margin-right: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); background: white; padding: 5px;" onerror="this.style.display=\'none\'; console.log(\'Logo加载失败: \' + this.src);">\n')
        html_file.write('<div>\n')
        html_file.write('<h1 style="margin: 0; color: white; font-size: 28px; font-weight: bold;">渲染医生</h1>\n')
        html_file.write('<p style="margin: 5px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">图形渲染分析工具</p>\n')
        html_file.write('</div>\n')
        html_file.write('</div>\n')
        html_file.write(' %s\n' % rdc_file)

        # 主要内容区域
        html_file.write('<div class="main-content">\n')
        
        # 1. 帧概览 - 美术资产分析
        self.writeFrameOverview(html_file, controller)
        
        # 2. API概览
        self.writeAPIOverview(html_file, controller)
        
        # 3. 资源概览
        self.writeResourceOverview(html_file, controller)
        


        # 4. 着色器概览已取消
        
        # 5. 绘制概览
        html_file.write('<div class="pass-section">\n')
        html_file.write('<div class="pass-header">\n')
        html_file.write('<div class="pass-title">🎯 绘制概览</div>\n')
        html_file.write('<div class="pass-stats">\n')
        html_file.write('<span class="stat-item">📊 总Pass数: %d</span>\n' % len(self.passes))
        html_file.write('</div>\n')
        html_file.write('</div>\n')
        html_file.write('<div class="pass-content-area">\n')
        for p in self.passes:
            p.writeIndexHtml(html_file, controller)
        html_file.write('</div>\n')
        html_file.write('</div>\n')
        


        html_file.write('</div>\n')  # main-content

        if not config['MINIMALIST']:
            html_file.write('<div class="usage-section">\n')
            html_file.write('<h2>📖 使用说明</h2>\n')
            html_file.write('<ul>\n')
            html_file.write('<li>按 <code>p</code> / <code>shift+p</code> 在通道间跳转</li>\n')
            html_file.write('<li>按 <code>s</code> / <code>shift+s</code> 在状态间跳转</li>\n')
            html_file.write('<li>按 <code>d</code> / <code>shift+d</code> 在绘制调用间跳转</li>\n')
            html_file.write('</ul>\n')
            html_file.write('</div>\n')

            html_file.write('<div class="summary-section">\n')
            html_file.write('<h2>📋 总结</h2>\n')
            if config['WRITE_PSO_DAG']:
                html_file.write('<p>• 实验功能 <a href="assets/dag.html">管道图</a></p>\n')
            html_file.write('<p>• RDC: %s</p>\n' % rdc_file)
            html_file.write('<p>• API: %s</p>\n' % pipelineTypes[api_prop.pipelineType])
            html_file.write('<p>• GPU: %s</p>\n' % GPUVendors[api_prop.vendor])
            html_file.write('</div>\n')

# Config section hidden




        html_file.write('\n</body>\n</html>')

        if config['WRITE_PSO_DAG']:
            try:
                self.writeDAG()
            except Exception as e:
                print(f"Warning: writeDAG failed: {e}")

    def exportResources(self, controller):
        print('^exportResources')
        
        # 复制logo文件到输出目录
        try:
            import shutil
            from pathlib import Path
            
            # 使用固定的D盘项目路径
            logo_src = Path(r'D:\render-doctor\src\logo.png')
            logo_dst = g_assets_folder / 'logo.png'
            
            if logo_src.exists():
                shutil.copy2(logo_src, logo_dst)
                print(f"✅ Logo已复制到: {logo_dst}")
            else:
                print(f"⚠️ 无法找到logo文件: {logo_src}")
                    
        except Exception as e:
            print(f"❌ 复制logo文件失败: {e}")
        
        for p in self.passes:
            p.exportResources(controller)
        print('$exportResources')

g_frame = Frame()

class Resource:
    pass

g_assets_folder = None
g_output_folder = None

def get_resource_filename(name, ext = 'txt'):
    return '%s.%s' % (name, ext)

def link_to_file(resource_name, file_name):
    return '[%s](%s)' % (resource_name, file_name)

def linkable_get_resource_filename(name, ext = 'txt'):
    return link_to_file(name, get_resource_filename(name, ext))

def linkable_ResID(id):
    return "[ResID_%s](#ResID_%s)" % (id, id)

def anchor_ResID(id):
    return "<a name=ResID_%s></a>ResID_%s" % (id, id)

def setup_rdc(filename, adb_mode = None):

    if adb_mode:
        # protocols = rd.GetSupportedDeviceProtocols()
        protocol_to_use = 'adb'
        protocol = rd.GetDeviceProtocolController(protocol_to_use)
        devices = protocol.GetDevices()

        if len(devices) == 0:
            raise RuntimeError(f"no {protocol_to_use} devices connected")

        # Choose the first device
        dev = devices[0]
        name = protocol.GetFriendlyName(dev)

        print(f"Running test on {dev} - named {name}")

        URL = protocol.GetProtocolName() + "://" + dev

    rd.InitialiseReplay(rd.GlobalEnvironment(), [])

    cap = rd.OpenCaptureFile()

    # Open a particular file - see also OpenBuffer to load from memory
    status = cap.OpenFile(rdc_file, '', None)
    print("cap.OpenFile")

    # Make sure the file opened successfully
    if status != rd.ReplayStatus.Succeeded:
        raise RuntimeError("Couldn't open file: " + str(status))

    # Make sure we can replay
    if not cap.LocalReplaySupport():
        raise RuntimeError("Capture cannot be replayed")

    # Initialise the replay
    status,controller = cap.OpenCapture(rd.ReplayOptions(), None)
    print("cap.OpenCapture")

    if status != rd.ReplayStatus.Succeeded:
        raise RuntimeError("Couldn't initialise replay: " + rd.ReplayStatus(status).name)

    return cap, controller

def get_expanded_marker_name():
    sep = ' / '
    return sep.join(g_markers)

def get_marker_name():
    if len(g_markers) > 0:
        name = g_markers[-1]
        if 'Colour_Pass' in name:
            return ''
        if len(g_markers) > 1 and name in ['Shadows.Draw', 'ShadowLoopNewBatcher.Draw', 'RenderLoop.Draw', 'RenderLoopNewBatcher.Draw']:
            # to make Unity reports prettier
            name = g_markers[-2]
        max_name_length = 40
        if len(name) > max_name_length:
            name = name[0 : max_name_length-3] + '...'
        return name
    return ''

# Define a recursive function for iterating over draws
def visit_action(controller, draw, level = 0):
    # hack level
    global g_markers, g_next_draw_will_add_state
    global api_full_log, api_short_log
    action_name = draw.GetName(sdfile)

    # print(action_name)
    if action_name == 'API Calls':
        pass

    needsPopMarker = False
    # print(rd.GLChunk.glPopGroupMarkerEXT)
    if draw.events:
        # api before this draw & including this draw
        for ev in draw.events:
            new_event = Event(controller, ev, level)
            State.current.addEvent(new_event)

        if draw.flags & rd.ActionFlags.Drawcall \
            or draw.flags & rd.ActionFlags.Dispatch \
            or draw.flags & rd.ActionFlags.MultiAction \
            or draw.flags & rd.ActionFlags.Clear \
            or draw.flags & rd.ActionFlags.Copy:
            new_draw = Draw(controller, draw, level)

            if g_next_draw_will_add_state:
                # and check duplicated binds...
                g_next_draw_will_add_state = False
                prev_draw = State.current.getLastDraw()
                if not prev_draw:
                    g_frame.addPass()
                elif not new_draw.sharesState(prev_draw):
                    g_frame.addPass()

            new_draw.collectPipeline(controller)
            State.current.addDraw(new_draw)
        elif draw.flags & rd.ActionFlags.PushMarker:
            # regime call, skip for now
            # TODO: leverate getSafeName()
            api_full_log.write('%s%04d %s\n' % ('    ' * level, draw.eventId, action_name))
            api_short_log.write('%s%04d %s\n' % ('    ' * level, draw.actionId, action_name))
            items = action_name.replace('|',' ').replace('(',' ').replace(')',' ').replace('-',' ').replace('=>',' ').replace('#',' ').split()
            name = '_'.join(items)

            g_markers.append(name)
            needsPopMarker = True

    # Iterate over the draw's children
    try:
        for i, child_draw in enumerate(draw.children):
            try:
                visit_action(controller, child_draw, level + 1)
            except Exception as e:
                print(f"Debug: Error processing child {i+1}/{len(draw.children)}: {e}")
                import traceback
                traceback.print_exc()
                continue
    except Exception as e:
        print(f"Debug: Error iterating draw children: {e}")
        import traceback
        traceback.print_exc()

    if needsPopMarker:
        g_markers.pop()

    return True

def get_texture_info(controller, resource_id):
    # struct TextureDescription
    if resource_id == rd.ResourceId.Null():
        return None

    textures = controller.GetTextures()
    for res in textures:
        if resource_id == res.resourceId:
            return res

    return None

resource_name_count = {}
resource_name_dict = {}

def get_resource_name(controller, resource_id, get_safe_name = True):
    if resource_id == rd.ResourceId.Null():
        return "NULL"

    if resource_id not in resource_name_dict:
        resource_name_dict[resource_id] = 'res_%d' % int(resource_id)

        resources = controller.GetResources()
        for res in resources:
            if resource_id == res.resourceId:
                name = res.name
                count = 0
                if name in resource_name_count:
                    resource_name_count[name] += 1
                    count = resource_name_count[name]
                else:
                    resource_name_count[name] = count

                if get_safe_name:
                    name = getSafeName(res.name)
                else:
                    name = res.name

                if count > 0:
                    name = '%s_%d' % (name, count)
                resource_name_dict[resource_id] = name

    return resource_name_dict[resource_id]

def generate_raw_data(controller):
    print('^generate_raw_data')
    try:
        # Start iterating from the first real draw as a child of markers
        # draw type = ActionDescription
        global API_TYPE
        api_prop = controller.GetAPIProperties()
        API_TYPE = api_prop.pipelineType
        print('API_TYPE', API_TYPE)

        actions = controller.GetRootActions()
        print(f"Debug: Found {len(actions)} root actions")
        
        # Iterate over all of the root drawcalls
        for i, d in enumerate(actions):
            try:
                print(f"Debug: Processing action {i+1}/{len(actions)}: {d.GetName(sdfile)}")
                visit_action(controller, d)
            except Exception as e:
                print(f"Debug: Error processing action {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print('$generate_raw_data')
    except Exception as e:
        print(f"Debug: Error in generate_raw_data: {e}")
        import traceback
        traceback.print_exc()

def generate_derived_data(controller):

    print('^generate_derived_data')

    print('$generate_derived_data')


def generate_viz(controller): 
    print('^generate_viz')
    g_frame.writeIndexHtml(index_html, controller)

    if not config['MINIMALIST']:
        for p in g_frame.passes:
            p.writeDetailHtml(index_html, controller)

    g_frame.exportResources(controller)
    print('$generate_viz')
    print("%s\n" % (report_name))

def print_var(v, indent = '', shader_name = '', setup_shader_doctor = False):
    # TODO: ugly
    if '[' in v.name or ']' in v.name:
        # v is a row of a matrix
        valstr = ''
        indent = ''
    else:
        if setup_shader_doctor:
            g_frame.shaders[shader_name]['uniforms'][v.name] = {
                'used': False
            }
        valstr = indent + v.name + "\n"

    if len(v.members) == 0:
        # leaf node
        for r in range(0, v.rows):
            valstr += indent + '  '

            for c in range(0, v.columns):
                index = r*v.columns + c
                if v.type == rd.VarType.Float:
                    if index < len(v.value.f32v):
                        valstr += '%.3f ' % v.value.f32v[index]
                    else:
                        print(f"Debug: Unity CBuffer - Index {index} out of range for f32v (length: {len(v.value.f32v)})")
                        print(f"Debug: Variable name: {v.name}, Type: {v.type}, Rows: {v.rows}, Columns: {v.columns}")
                        valstr += 'N/A '
                elif v.type == rd.VarType.Double:
                    if index < len(v.value.f64v):
                        valstr += '%.3g ' % v.value.f64v[index]
                    else:
                        valstr += 'N/A '
                elif v.type == rd.VarType.SInt:
                    if index < len(v.value.s32v):
                        valstr += '%d ' % v.value.s32v[index]
                    else:
                        valstr += 'N/A '
                elif v.type == rd.VarType.UInt:
                    if index < len(v.value.u32v):
                        valstr += '%d ' % v.value.u32v[index]
                    else:
                        valstr += 'N/A '

            if r < v.rows-1:
                valstr += "\n"

    for member in v.members:
        valstr += print_var(member, indent + '    ')

    valstr += '\n'

    return valstr

def get_cbuffer_contents(controller, stage, shader_name, refl, program_name):
    pipe = controller.GetPipelineState()

    contents = ''

    api_state = pipe.GetGraphicsPipelineObject()
    if stage == rd.ShaderStage.Compute:
        api_state = pipe.GetComputePipelineObject()

    shader = pipe.GetShader(stage)

    setup_shader_doctor = False
    if shader not in g_frame.shaders:
        setup_shader_doctor = True
        g_frame.shaders[shader_name] = {
            'state': program_name,
            'type': ShaderStage(stage).name,
            'uniforms': {}
        }

    if API_TYPE != rd.GraphicsAPI.OpenGL:
        setup_shader_doctor = False

    for slot in range(0, 4):
        try:
            if hasattr(pipe, 'GetConstantBuffer'):
                cb = pipe.GetConstantBuffer(stage, slot, 0)
            else:
                print(f"Debug: PipeState object has no GetConstantBuffer method")
                break
        except Exception as e:
            print(f"Debug: Error getting constant buffer for stage {stage}, slot {slot}: {e}")
            break

        ver = rd.GetVersionString()
        from distutils.version import LooseVersion
        if LooseVersion(ver) >= LooseVersion('1.17'):
            cbufferVars = controller.GetCBufferVariableContents(api_state, pipe.GetShader(stage),
                                                                stage, pipe.GetShaderEntryPoint(stage),
                                                                slot, cb.resourceId,
                                                                cb.byteOffset, cb.byteSize)
        else:
            cbufferVars = controller.GetCBufferVariableContents(api_state,
                                                                pipe.GetShader(stage),
                                                                pipe.GetShaderEntryPoint(stage), slot,
                                                                cb.resourceId, cb.byteOffset, cb.byteSize)

        if not cbufferVars:
            break

        for v in cbufferVars:
            contents += print_var(v, shader_name = shader_name, setup_shader_doctor = setup_shader_doctor)
        contents += '\n----------------------------------\n'

    if setup_shader_doctor:
        rawBytes = str(refl.rawBytes, 'utf-8')
        for k,v in g_frame.shaders[shader_name]['uniforms'].items():
            if rawBytes.count(k) > 1:
                # uniform definition itself cost one occurence
                v['used'] = True

    return contents

def fetch_gpu_counters(controller):
    global g_draw_durations
    counter_type = rd.GPUCounter.EventGPUDuration
    results = controller.FetchCounters([counter_type])
    counter_desc = controller.DescribeCounter(counter_type)

    for r in results:
        id = r.eventId

        if counter_desc.resultByteWidth == 4:
            val = r.value.f
        else:
            val = r.value.d

        g_draw_durations[id] = val

def rdc_main(controller):
    global g_assets_folder
    global report_name
    global index_html
    global api_full_log, api_short_log
    global config
    global sdfile

    sdfile = controller.GetStructuredFile()

    config_json = Path(os.getenv('APPDATA'), 'rd.json')

    try:
        with open(config_json) as f:
            config = json.load(f)
    except Exception as e:
        with open(config_json, 'w', encoding='utf-8') as f:
            f.write(json.dumps(config, indent=4))

    try:
        api_full_log = open(g_assets_folder / 'api_full.txt',"w", encoding='utf-8')
        api_short_log = open(g_assets_folder / 'api_short.txt',"w", encoding='utf-8')

        report_name = g_output_folder / 'index.html'

        fetch_gpu_counters(controller)
        generate_raw_data(controller)
        generate_derived_data(controller)

        index_html = open(report_name,"w", encoding='utf-8')
        try:
            generate_viz(controller)
        finally:
            index_html.close()

        api_full_log.close()
        api_short_log.close()
    except Exception as e:
        print(f"Error in rdc_main: {str(e)}")
        import traceback
        traceback.print_exc()

def shutdown_rdc(cap, controller):
    controller.Shutdown()
    cap.Shutdown()
    rd.ShutdownReplay()

if 'pyrenderdoc' in globals():
    rdc_file = pyrenderdoc.GetCaptureFilename()
    absolute = WindowsPath(rdc_file).absolute()
    # index.html放在外面，其他文件放在assets子文件夹
    g_output_folder = absolute.parent / absolute.stem
    g_assets_folder = g_output_folder / 'assets'
    if False:
        from datetime import datetime
        g_output_folder = g_output_folder + '-' + datetime.now().strftime("%Y-%b-%d-%H-%M-%S")
        g_assets_folder = g_output_folder / 'assets'
    g_output_folder.mkdir(parents=True, exist_ok=True)
    g_assets_folder.mkdir(parents=True, exist_ok=True)

    pyrenderdoc.Replay().BlockInvoke(rdc_main)
else:
    if len(sys.argv) > 1:
        rdc_file = sys.argv[1]
    absolute = WindowsPath(rdc_file).absolute()
    # index.html放在外面，其他文件放在assets子文件夹
    g_output_folder = absolute.parent / absolute.stem
    g_assets_folder = g_output_folder / 'assets'
    g_output_folder.mkdir(parents=True, exist_ok=True)
    g_assets_folder.mkdir(parents=True, exist_ok=True)

    cap, controller = setup_rdc(rdc_file)
    rdc_main(controller)
    shutdown_rdc(cap, controller)
