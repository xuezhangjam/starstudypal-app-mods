"""Connect existing question spans and the answer title to the same blank index."""
from build import B, OWN, PAT, long, write

BEAN = 'Lcom/hailiang/question/data/QuestionBean;'
BUILDER = 'Lcom/hailiang/question/text/QuestionSpannableBuilder;'
LISTENER = 'Lcom/hailiang/question/listener/InsertEventListener;'
DISPLAY = 'Lcom/hailiang/workcloud/student/shareui/uicore/question/QuestionComponentDisplay;'
BLANK = OWN + 'BlankLabels;'
FILL = 'Lcom/hailiang/xxb/question/ui/v3/plugins/FillInsertRenderPluginV3;'
NATIVE_FILL = 'Lcom/hailiang/question/build/component/plugins/insert/FillInsertRenderPlugin;'
GENERATOR = 'Lcom/hailiang/question/generator/InsertGeneratorHelper;'
BOARD = 'Lcom/hailiang/workcloud/student/shareui/work/select/QuestionAnswerBoardAreaKt;'


def transform(owner, signature, rewrite, base):
    path = 'smali/' + owner[1:-1] + '.smali'
    original = long(base / path).read_text('utf8')
    matches = [m for m in PAT.finditer(original) if m[1].split()[-1].startswith(signature)]
    assert len(matches) == 1, (owner, signature)
    method, = matches
    write(B / 'work5' / path, original[:method.start()] + rewrite(method[0]) + original[method.end():])


def title(method):
    old = f'    invoke-static {{v2, v12, v10}}, {BLANK}->boardTitle(Ljava/lang/String;{BEAN}I)Ljava/lang/String;'
    assert method.count(old) == 1
    return method.replace(old, f'''    move-object/from16 v11, p1

    invoke-static {{v2, v12, v10, v11}}, {BLANK}->boardTitle(Ljava/lang/String;{BEAN}I{DISPLAY})Ljava/lang/String;''')


def preview_blank(method):
    old = f'    invoke-static {{p5, p0, p4}}, {BLANK}->appendStemLabel({BUILDER}{BEAN}I)V'
    assert method.count(old) == 1
    return method.replace(old, f'''    const/16 v0, 0x82

    invoke-static {{p5, p0, p4, p7, v0}}, {BLANK}->renderInline({BUILDER}{BEAN}I{LISTENER}I)Z

    move-result v0

    if-eqz v0, :cond_0

    return v0''')


def keyboard_blank(method):
    # The original keyboard input span stays attached and handles focus and editing.
    start = method.index('    :cond_f\n')
    end = method.index('    if-eqz v7, :cond_10', start)
    marker = '    invoke-static/range {v0 .. v6},'
    call = method.index(marker, start, end)
    assert 'appendIdxTag--2Osg14$default(' in method[call:end]
    return method[:call] + f'''    const/16 v5, 0x40

    invoke-static {{v1, v9, v2, v4, v5}}, {BLANK}->renderInline({BUILDER}{BEAN}I{LISTENER}I)Z

    move-result v5

    if-nez v5, :number_tag_done

    const/4 v5, 0x4

''' + method[call:end] + '    :number_tag_done\n' + method[end:]


def review_blank(method):
    anchor = '    :goto_0\n'
    assert method.count(anchor) == 1
    return method.replace(anchor, anchor + f'''
    invoke-static {{p2, p4}}, {BLANK}->label({BEAN}I)Ljava/lang/String;

    move-result-object v0

    if-eqz v0, :blank_label_ready

    move-object p0, v0

    :blank_label_ready
''', 1)


def patch(base):
    transform(BOARD, 'QuestionAnswerBoardArea-pglpRAY(', title, base)
    transform(FILL, 'render-NjoSL3Q(', preview_blank, base)
    transform(NATIVE_FILL, 'render-NjoSL3Q(', keyboard_blank, base)
    transform(GENERATOR, 'appendHandwriteIdxSpan-OGs1dP0(', review_blank, base)
