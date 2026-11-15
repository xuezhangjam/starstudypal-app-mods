package com.hljzjx.classroom.reentry;

import android.view.View;
import com.nice.room.R;

public final class CompactQuestions {
    private CompactQuestions() {}

    public static void hidePptReturn(View root, View button) {
        if (button != null && root.findViewById(R.id.draggable_layout) != null
                && button.getVisibility() != View.GONE) {
            button.setVisibility(View.GONE);
        }
    }
}
