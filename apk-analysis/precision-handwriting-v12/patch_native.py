"""Patch only the v11 entry points that route writing and measure the panes."""
import re

from build import B, OWN, PAT, long, write

QUESTION = 'Lcom/hailiang/question/widget/view/QuestionHandwriteView;'
TOUCH = 'Landroid/view/MotionEvent;'
PEN_HELPER = 'Lcom/hailiang/question/util/HandWriteHelper;'
POLICY = 'Landroidx/compose/ui/layout/MeasurePolicy;'
WRITING = OWN + 'WritingTouch;'
BLANK = OWN + 'BlankLabels;'
BEAN = 'Lcom/hailiang/question/data/QuestionBean;'
BUILDER = 'Lcom/hailiang/question/text/QuestionSpannableBuilder;'
SPAN = 'Lcom/hailiang/question/text/span/ShortTextInputSpan;'
DRAWABLE = 'Lcom/hailiang/question/widget/view/TextRoundRectDrawable;'


def transform(relative, name, rewrite, base, *, preserve_prior_edits=False):
    path = 'smali/' + relative + '.smali'
    output = B / 'work5' / path
    original = long(output if preserve_prior_edits else base / path).read_text('utf8')
    prefix = name if '(' in name else name + '('
    methods = [m for m in PAT.finditer(original) if m[1].split()[-1].startswith(prefix)]
    assert len(methods) == 1, (relative, name, len(methods))
    method, = methods
    write(output, original[:method.start()] + rewrite(method[0]) + original[method.end():])


def writing_bridge(method):
    header = f'.method public dispatchTouchEvent({TOUCH})Z'
    assert method.startswith(header)
    method = method.replace(header, f'.method public final modDispatchWritingEvent({TOUCH})Z', 1)
    start = method.index('    :cond_0\n') + len('    :cond_0\n')
    end = method.index('    :cond_1\n', start) + len('    :cond_1\n')
    assert 'executeAutoSave()V' in method[start:end]
    method = method[:start] + method[end:]
    method = method.replace('    :goto_0\n', '', 1)
    needle = '    move-result v2\n'
    assert method.count(needle) == 1
    method = method.replace(needle, needle + f'''
    if-eqz p1, :ink_touch_complete

    invoke-virtual {{p1}}, {TOUCH}->getActionMasked()I

    move-result v0

    const/4 v1, 0x1

    if-eq v0, v1, :ink_save

    const/4 v1, 0x3

    if-ne v0, v1, :ink_touch_complete

    :ink_save
    invoke-virtual {{p1}}, {TOUCH}->getPointerCount()I

    move-result v0

    const/4 v1, 0x1

    if-ne v0, v1, :ink_touch_complete

    sget-object v0, {PEN_HELPER}->INSTANCE:{PEN_HELPER}

    invoke-virtual {{v0, p1}}, {PEN_HELPER}->isPenEvent({TOUCH})Z

    move-result v0

    if-eqz v0, :ink_touch_complete

    invoke-direct {{p0}}, {QUESTION}->executeAutoSave()V

    :ink_touch_complete
''', 1)
    return f'''{header}
    .locals 1

    invoke-static {{p0, p1}}, {WRITING}->dispatch({QUESTION}{TOUCH})Z

    move-result v0

    return v0
.end method

{method}'''


def forget(method):
    marker = f'    invoke-static {{p0}}, {OWN}InkHistory;->forget({QUESTION})V'
    assert method.count(marker) == 1
    return method.replace(marker, f'    invoke-static {{p0}}, {WRITING}->forget({QUESTION})V\n\n' + marker)


def answer_panes(method):
    match = re.search(
        r'(?m)^    invoke-static .*?BoxKt;->maybeCachedBoxMeasurePolicy[^\n]+\n\n'
        r'    move-result-object (v\d+)\n',
        method,
    )
    assert match and 'getTopStart()' in method[match.start() - 500:match.start()]
    register = match[1]
    return method[:match.end()] + f'''
    invoke-static {{{register}}}, {OWN}AnsweringPanes;->withAnswerWidth({POLICY}){POLICY}

    move-result-object {register}
''' + method[match.end():]


def blank_title(method):
    start = method.index('->getAnswer_area_title(')
    needle = '    move-result-object v16\n'
    end = method.index(needle, start) + len(needle)
    assert 'stringResource(' in method[start:end]
    return method[:end] + f'''
    move-object/from16 v2, v16

    move/from16 v10, p7

    invoke-static {{v2, v12, v10}}, {BLANK}->boardTitle(Ljava/lang/String;{BEAN}I)Ljava/lang/String;

    move-result-object v16
''' + method[end:]


def numbered_input_span(method):
    needle = '    :goto_1\n'
    assert method.count(needle) == 1
    return method.replace(needle, needle + f'''
    iget-object v0, p0, {SPAN}->question:{BEAN}

    iget v1, p0, {SPAN}->idx:I

    invoke-static {{v0, v1}}, {BLANK}->label({BEAN}I)Ljava/lang/String;

    move-result-object v0

    if-eqz v0, :native_span_invalidate

    iget-object v1, p0, {SPAN}->drawable:{DRAWABLE}

    invoke-virtual {{v1, v0}}, {DRAWABLE}->setString(Ljava/lang/String;)V

    :native_span_invalidate
''', 1)


def numbered_empty_span(method):
    needle = '    if-eq p1, p2, :cond_0\n'
    assert method.count(needle) == 1
    # For a fill-in question p0 still holds the QuestionBean at this branch.
    method = method.replace(needle, '    if-eq p1, p2, :number_fill\n', 1)
    return method.replace('    .line 44\n    :cond_0\n', f'''
    :number_fill
    invoke-static {{p5, p0, p4}}, {BLANK}->appendStemLabel({BUILDER}{BEAN}I)V

    .line 44
    :cond_0
''', 1)


def patch(base):
    transform(QUESTION[1:-1], 'dispatchTouchEvent', writing_bridge, base)
    for method in ('onDetachedFromWindow', 'reset'):
        transform(QUESTION[1:-1], method, forget, base, preserve_prior_edits=True)
    transform(PEN_HELPER[1:-1], 'isPenEvent', lambda _: f'''.method public final isPenEvent({TOUCH})Z
    .locals 1

    invoke-static {{p1}}, {WRITING}->isPenEvent({TOUCH})Z

    move-result v0

    return v0
.end method''', base)
    transform(
        'com/hailiang/workcloud/student/shareui/work/select/SelectQuestionPanel_androidKt',
        'SelectQuestionPanelAnswering', answer_panes, base,
    )
    transform(
        'com/hailiang/workcloud/student/shareui/work/select/QuestionAnswerBoardAreaKt',
        'QuestionAnswerBoardArea-pglpRAY', blank_title, base,
    )
    transform(SPAN[1:-1], 'updateState(Lcom/hailiang/question/consts/InsertStatus;)', numbered_input_span, base)
    transform(
        'com/hailiang/xxb/question/ui/v3/plugins/FillInsertRenderPluginV3',
        'render-NjoSL3Q', numbered_empty_span, base,
    )
