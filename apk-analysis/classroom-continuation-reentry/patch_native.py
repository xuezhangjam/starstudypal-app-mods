"""Bind result requests, restored editors and compact layouts to the new helpers."""
from build import B, PAT, long, write

ASK = 'com/nice/room/ui/roomlive/fragment/ask/'
ANSWER = 'L' + ASK + 'answer/QuestionAskAnswerBaseFragment;'
RESULT = 'L' + ASK + 'result/QuestionAskOptionResultFragment;'
REQUEST = 'L' + ASK + 'QuestionAskViewModel$getAnswerDetail$1;'
PPT = 'Lcom/hljzjx/classroom/mod/QuestionPptReturn$State;'
RECOVERY = 'Lcom/hljzjx/classroom/reentry/ChoiceRecovery;'
COMPACT = 'Lcom/hljzjx/classroom/reentry/CompactQuestions;'
DETAIL = 'Lcom/hailiang/xxb/room/server/entity/ask/QuestionAskDetail;'
VIEW = 'Landroid/view/View;'


def transform(dex, base, owner, name, rewrite, *, reuse=False, extra_field=False):
    path = 'smali/' + owner[1:-1] + '.smali'
    destination = B / f'work{dex}' / path
    original = long(destination if reuse else base / path).read_text('utf8')
    matches = [m for m in PAT.finditer(original) if m[1].split()[-1].startswith(name + '(')]
    assert len(matches) == 1, (owner, name)
    method, = matches
    output = original[:method.start()] + rewrite(method[0]) + original[method.end():]
    if extra_field:
        anchor = '.field label:I'
        assert output.count(anchor) == 1
        output = output.replace(anchor, anchor + '\n\n.field private modRequestUser:J')
    write(destination, output)


def tag_detail(method):
    assert '.locals 5' in method and method.count('    :cond_1\n') == 1
    method = method.replace('.locals 5', '.locals 8', 1).replace('    :cond_1\n', f'''    :cond_1
    invoke-static {{}}, Lcom/hailiang/common/util/AppRuntimeData;->getUserId()J

    move-result-wide v1

    iput-wide v1, p0, {REQUEST}->modRequestUser:J

    const/4 v2, 0x1
''', 1)
    anchor = f'    iget-object p0, p0, {REQUEST}->this$0:'
    assert method.count(anchor) == 1
    return method.replace(anchor, f'''    iget-object v0, p1, Lcom/hailiang/libhttp/BaseHttpResult;->data:Ljava/lang/Object;

    iget-wide v1, p0, {REQUEST}->$classroomId:J

    iget-wide v3, p0, {REQUEST}->$askId:J

    iget-wide v5, p0, {REQUEST}->modRequestUser:J

    invoke-static/range {{v0 .. v6}}, {RECOVERY}->stamp(Ljava/lang/Object;JJJ)V

''' + anchor, 1)


def observe_detail(method):
    return entry(method, f'    invoke-static {{p0, p1, p2}}, {RECOVERY}->onResult({VIEW}{RESULT}{DETAIL})V')


def prepare(method):
    return entry(method, f'    invoke-static {{p0}}, {RECOVERY}->prepare({ANSWER})V')


def skip_original_restore(method):
    assert '.locals 0' in method
    anchor = f'    invoke-direct {{p0}}, {ANSWER}->restoreLocalData()V'
    assert method.count(anchor) == 1
    method = method.replace('.locals 0', '.locals 1', 1).replace(anchor, f'''    invoke-static {{p0}}, {RECOVERY}->recovered({ANSWER})Z

    move-result v0

    if-nez v0, :restore_finished

''' + anchor)
    return method.replace('    return-void', '    :restore_finished\n    return-void')


def compact_return(method):
    return entry(method, f'''    iget-object v0, p0, {PPT}->root:{VIEW}

    iget-object v1, p0, {PPT}->entry:Landroid/widget/TextView;

    invoke-static {{v0, v1}}, {COMPACT}->hidePptReturn({VIEW}{VIEW})V''')


def entry(method, instructions):
    start = method.index('\n\n') + 2
    assert '.locals' in method[:start]
    return method[:start] + instructions + '\n\n' + method[start:]


def patch(base4, base10):
    transform(4, base4, REQUEST, 'invokeSuspend', tag_detail, extra_field=True)
    transform(4, base4, RESULT, 'onViewCreated$lambda$2', observe_detail)
    transform(4, base4, ANSWER, 'observeData', prepare)
    transform(4, base4, ANSWER, 'onFragmentFirstVisible', skip_original_restore, reuse=True)
    transform(10, base10, PPT, 'visibility', compact_return)
