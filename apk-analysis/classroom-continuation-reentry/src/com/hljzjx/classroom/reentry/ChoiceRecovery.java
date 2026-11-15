package com.hljzjx.classroom.reentry;

import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.FrameLayout;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import com.hailiang.common.util.AppRuntimeData;
import com.hailiang.xxb.room.server.entity.ask.QuestionAskAnswer;
import com.hailiang.xxb.room.server.entity.ask.QuestionAskDetail;
import com.hailiang.xxb.room.server.entity.ask.QuestionAskItem;
import com.hailiang.xxb.room.server.entity.ask.QuestionAskType;
import com.hljzjx.classroom.mod.HandwriteContinuation;
import com.hljzjx.classroom.mod.QuestionOverlayLayout;
import com.hljzjx.classroom.mod.QuestionPptReturn;
import com.nice.room.R;
import com.nice.room.ui.roomlive.fragment.ask.answer.QuestionAskAnswerBaseFragment;
import com.nice.room.ui.roomlive.fragment.ask.answer.QuestionAskOptionFragment;
import com.nice.room.ui.roomlive.fragment.ask.data.QuestionAskSubmitItem;
import com.nice.room.ui.roomlive.fragment.ask.result.QuestionAskOptionResultFragment;
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.WeakHashMap;

/** Restore an ended choice editor using the authenticated native result request. */
public final class ChoiceRecovery {
    private static final String RECOVERED_OWNER = "mod_recovered_choice_owner";
    private static final ArrayList<Response> RESPONSES = new ArrayList<>();
    private static final WeakHashMap<View, Boolean> SEEDED = new WeakHashMap<>();

    private ChoiceRecovery() {}

    public static synchronized void stamp(Object payload, long classroom, long ask, long user) {
        if (!(payload instanceof QuestionAskDetail) || classroom <= 0 || ask <= 0 || user <= 0) return;
        RESPONSES.removeIf(response -> response.payload.get() == null || response.payload.get() == payload);
        if (RESPONSES.size() >= 16) RESPONSES.remove(0);
        RESPONSES.add(new Response((QuestionAskDetail) payload, classroom, ask, user));
    }

    private static synchronized Response find(QuestionAskDetail payload) {
        for (Response response : RESPONSES) if (response.payload.get() == payload) return response;
        return null;
    }

    public static void onResult(View root, QuestionAskOptionResultFragment result, QuestionAskDetail detail) {
        Response response = find(detail);
        if (response != null && response.matches(result)) {
            root.post(() -> restore(root, result, detail, response));
        }
    }

    private static void restore(View root, QuestionAskOptionResultFragment result, QuestionAskDetail detail, Response response) {
        if (!response.matches(result) || result.getView() != root || !root.isAttachedToWindow()
                || !result.isAdded() || !root.isShown()
                || !(root.getParent() instanceof FrameLayout)
                || ((FrameLayout) root.getParent()).getId() != R.id.fragment_container
                || result.getActivity() == null
                || !result.getActivity().getClass().getName().equals("com.nice.room.ui.RoomLiveActivity")) return;

        FragmentManager manager = result.getParentFragmentManager();
        if (manager.isStateSaved()) return;
        QuestionAskOptionFragment draft = null;
        for (Fragment fragment : manager.getFragments()) {
            if (!(fragment instanceof QuestionAskAnswerBaseFragment)) continue;
            QuestionAskAnswerBaseFragment answer = (QuestionAskAnswerBaseFragment) fragment;
            if (answer.getClassroomId() != response.classroom || answer.getAskId() != response.ask) continue;
            if (!(answer instanceof QuestionAskOptionFragment)) return;
            if (!recovered(answer)) {
                if (answer.getSubmitted() || answer.getFinished()) {
                    HandwriteContinuation.stateChanged(answer);
                    HandwriteContinuation.attachResult(result, root);
                }
                return;
            }
            if (answer.requireArguments().getLong(RECOVERED_OWNER) != response.user) return;
            draft = (QuestionAskOptionFragment) answer;
            if (SEEDED.containsKey(draft.getView())) return;
            break;
        }
        if (draft == null && QuestionOverlayLayout.covered(root)) return;

        Draft data = buildDraft(detail, response.user);
        if (data == null) return;
        boolean created = false;
        try {
            if (draft == null) {
                draft = QuestionAskOptionFragment.Companion.newInstance(
                        response.classroom, detail.getType(), response.ask, data.titles.size(),
                        detail.getOptionNumber(), data.titles, 0, detail.getAnswerTimeLimit(), data.images);
                draft.requireArguments().putLong(RECOVERED_OWNER, response.user);
                prepare(draft);
                manager.beginTransaction().add(R.id.fragment_container, draft, "mod_recovered_choice").commitNow();
                created = true;
            }
            View draftRoot = draft.getView();
            if (draftRoot == null || draftRoot.getParent() != root.getParent()) return;
            QuestionPptReturn.suspend(draftRoot);
            draft.restoreData(data.items);
            HandwriteContinuation.stateChanged(draft);
            HandwriteContinuation.attachResult(result, root);
            SEEDED.put(draftRoot, true);
        } catch (RuntimeException problem) {
            Log.w("ChoiceRecovery", "Could not restore the choice editor", problem);
            if (created && draft.isAdded()) manager.beginTransaction().remove(draft).commitAllowingStateLoss();
        }
    }

    /** Recreated fragments must never restart the original timed submission path. */
    public static boolean recovered(QuestionAskAnswerBaseFragment fragment) {
        Bundle args = fragment.getArguments();
        return args != null && args.getLong(RECOVERED_OWNER) > 0;
    }

    public static void prepare(QuestionAskAnswerBaseFragment fragment) {
        if (recovered(fragment)) {
            fragment.setSubmitted(true);
            fragment.setFinished(true);
        }
    }

    static Draft buildDraft(QuestionAskDetail detail, long user) {
        boolean single = detail.getType() == QuestionAskType.OPTION.getValue();
        if (user <= 0 || (!single && detail.getType() != QuestionAskType.OPTION_MULTI.getValue())) return null;
        List<QuestionAskItem> rows = detail.getAskList();
        int optionCount = detail.getOptionNumber();
        int questionCount = detail.getQuestionNumber();
        if (rows == null || rows.isEmpty() || (questionCount > 0 && rows.size() != questionCount)
                || optionCount <= 0 || optionCount > 26) return null;
        Draft draft = new Draft();
        HashSet<Long> seen = new HashSet<>();
        for (QuestionAskItem row : rows) {
            if (row == null || row.getAskTitleId() <= 0 || !seen.add(row.getAskTitleId())) return null;
            long title = row.getAskTitleId();
            draft.titles.add(title);
            QuestionAskAnswer own = null;
            List<QuestionAskAnswer> answers = row.getAskAnswerList();
            if (answers != null) for (QuestionAskAnswer answer : answers) {
                if (answer != null && answer.getStudentId() == user
                        && (answer.getAskTitleId() == title || answer.getAskTitleId() == 0)
                        && (own == null || answer.getAskAnswerId() > own.getAskAnswerId())) own = answer;
            }
            if (own == null || own.getAnswerOption() == null || own.getAnswerOption().isEmpty()) continue;
            ArrayList<Integer> options = new ArrayList<>(own.getAnswerOption());
            if (single && options.size() != 1) return null;
            for (Integer index : options) if (index == null || index <= 0 || index > optionCount) return null;
            draft.items.add(new QuestionAskSubmitItem(title, options, null, own.getAnswerTime(), 0, user));
        }
        if (detail.getScreenshotUrlList() != null) draft.images.addAll(detail.getScreenshotUrlList());
        return draft;
    }

    static final class Draft {
        final ArrayList<Long> titles = new ArrayList<>();
        final ArrayList<QuestionAskSubmitItem> items = new ArrayList<>();
        final ArrayList<String> images = new ArrayList<>();
    }

    private static final class Response {
        final WeakReference<QuestionAskDetail> payload;
        final long classroom, ask, user;

        Response(QuestionAskDetail payload, long classroom, long ask, long user) {
            this.payload = new WeakReference<>(payload);
            this.classroom = classroom;
            this.ask = ask;
            this.user = user;
        }

        boolean matches(QuestionAskOptionResultFragment result) {
            return user == AppRuntimeData.getUserId()
                    && classroom == result.getClassroomId() && ask == result.getAskId();
        }
    }
}
