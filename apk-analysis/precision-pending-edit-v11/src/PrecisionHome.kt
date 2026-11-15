@file:OptIn(androidx.compose.material3.ExperimentalMaterial3ExpressiveApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class,
    androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
package com.hailiang.workcloud.student.md3e.v3

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hailiang.workcloud.student.shareui.home.*
import com.hailiang.workcloud.student.home.*
import com.hailiang.workcloud.student.shareui.core.components.LoadMoreState
import kotlinx.coroutines.flow.distinctUntilChanged

/** View-only replacement. Every server selection/action goes to the original callback. */
@Composable
fun HomeSurface(state: HomeUiState, userName: String,
    onSubject: (Long?) -> Unit, onFilter: (SchoolworkFilterStatus?) -> Unit,
    onRefresh: () -> Unit, onLoadMore: () -> Unit, onOpen: (HomeworkUiModel) -> Unit) {
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.surface) {
        if (state !is HomeUiState.Success) {
            Box(Modifier.fillMaxSize().safeDrawingPadding(), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    LoadingIndicator(); Text("正在加载作业", style = MaterialTheme.typography.bodyLarge)
                }
            }
        } else {
            BoxWithConstraints(Modifier.fillMaxSize().safeDrawingPadding()) {
                val rail = maxWidth >= 720.dp
                val expanded = maxWidth >= 1500.dp
                Row(Modifier.fillMaxSize()) {
                    if (rail) key(expanded) { SubjectRail(state, expanded, onSubject) }
                    Column(Modifier.weight(1f).fillMaxHeight()) {
                        HomeHeader(state, userName, onRefresh)
                        if (!rail) SubjectChips(state, onSubject)
                        StatusFilters(state.getSelectedFilter(), onFilter)
                        HomeworkFeed(state, onRefresh, onLoadMore, onOpen)
                    }
                }
            }
        }
    }
}

@Composable
private fun HomeHeader(state: HomeUiState.Success, userName: String, refresh: () -> Unit) {
    val subject = state.getSubjectTabs().firstOrNull { it.getId() == state.getSelectedSubjectId() }?.getLabel() ?: "首页"
    Row(Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(if (state.getSelectedSubjectId() == null) "精准作业" else "$subject 作业",
                style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold,
                maxLines = 2, overflow = TextOverflow.Ellipsis)
            Text("${userName.ifBlank { "同学" }} · 作业与订正",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        IconButton(onClick = refresh, enabled = !state.isRefreshing(), modifier = Modifier.size(48.dp)) {
            if (state.isRefreshing()) CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp)
            else Icon(Icons.Filled.Refresh, contentDescription = "刷新作业")
        }
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer, modifier = Modifier.size(44.dp)) {
            Box(contentAlignment = Alignment.Center) { Icon(Icons.Filled.Person, contentDescription = null) }
        }
    }
}

@Composable
private fun SubjectRail(state: HomeUiState.Success, expanded: Boolean, choose: (Long?) -> Unit) {
    val nav = rememberWideNavigationRailState(if (expanded) WideNavigationRailValue.Expanded else WideNavigationRailValue.Collapsed)
    WideNavigationRail(modifier = Modifier.fillMaxHeight(), state = nav, windowInsets = WindowInsets(0),
        header = {
            Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Surface(shape = MaterialTheme.shapes.large, color = MaterialTheme.colorScheme.primaryContainer,
                    contentColor = MaterialTheme.colorScheme.onPrimaryContainer) {
                    Icon(Icons.AutoMirrored.Filled.MenuBook, null, Modifier.padding(14.dp).size(28.dp))
                }
                if (expanded) Text("学科", style = MaterialTheme.typography.titleMedium)
            }
        }) {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            state.getSubjectTabs().forEach { tab ->
                WideNavigationRailItem(selected = tab.getId() == state.getSelectedSubjectId(), onClick = { choose(tab.getId()) },
                    icon = { SubjectIcon(tab.getLabel(), tab.getId() == null, if (tab.getId() == null) state.getTotalCount() else 0) },
                    label = { Text(tab.getLabel(), maxLines = 1) }, railExpanded = expanded,
                    modifier = Modifier.semantics { stateDescription = if (tab.getId() == state.getSelectedSubjectId()) "已选择" else "未选择" })
            }
        }
    }
}

@Composable
private fun SubjectIcon(label: String, home: Boolean, count: Int = 0) {
    BadgedBox(badge = { if (count > 0) Badge(containerColor = MaterialTheme.colorScheme.primaryContainer, contentColor = MaterialTheme.colorScheme.onPrimaryContainer) {
        Text(if (count > 99) "99+" else count.toString())
    } }) {
        Icon(subjectGraphic(label, home), null)
    }
}

private fun subjectGraphic(label: String, home: Boolean = false): ImageVector = when {
    home -> Icons.Filled.Home
    label.contains("化学") -> Icons.Filled.Science
    label.contains("物理") -> Icons.Filled.Bolt
    label.contains("生物") -> Icons.Filled.Biotech
    label.contains("历史") -> Icons.Filled.HistoryEdu
    label.contains("地理") -> Icons.Filled.Public
    label.contains("数学") -> Icons.Filled.Calculate
    label.contains("英语") -> Icons.Filled.Translate
    else -> Icons.AutoMirrored.Filled.MenuBook
}

@Composable
private fun SubjectChips(state: HomeUiState.Success, choose: (Long?) -> Unit) {
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 24.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        state.getSubjectTabs().forEach { tab ->
            FilterChip(selected = tab.getId() == state.getSelectedSubjectId(), onClick = { choose(tab.getId()) },
                shape = MaterialTheme.shapes.extraLarge,
                label = { Text(tab.getLabel()) }, leadingIcon = { SubjectIcon(tab.getLabel(), tab.getId() == null, if (tab.getId() == null) state.getTotalCount() else 0) },
                modifier = Modifier.heightIn(min = 48.dp))
        }
    }
}

@Composable
private fun StatusFilters(selected: SchoolworkFilterStatus?, choose: (SchoolworkFilterStatus?) -> Unit) {
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 24.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
        listOf(null, SchoolworkFilterStatus.PENDING_SUBMIT, SchoolworkFilterStatus.PENDING_CORRECTION, SchoolworkFilterStatus.AI_CHECK_FAILED).forEach { value ->
            FilterChip(selected = selected == value, onClick = { choose(value) }, label = { Text(filterName(value)) },
                shape = MaterialTheme.shapes.extraLarge,
                leadingIcon = if (selected == value) {{ Icon(Icons.Filled.Check, null, Modifier.size(18.dp)) }} else null,
                modifier = Modifier.heightIn(min = 48.dp))
        }
    }
}

fun filterName(value: SchoolworkFilterStatus?): String = when(value) {
    SchoolworkFilterStatus.PENDING_SUBMIT -> "待提交"
    SchoolworkFilterStatus.PENDING_CORRECTION -> "待订正"
    SchoolworkFilterStatus.AI_CHECK_FAILED -> "批阅失败"
    else -> "全部"
}
fun statusName(value: HomeworkStatus): String = when(value) {
    HomeworkStatus.PENDING_SUBMIT -> "待提交"
    HomeworkStatus.OVERDUE -> "已截止"
    HomeworkStatus.PENDING_CORRECTION -> "待订正"
    HomeworkStatus.GRADING -> "批阅中"
    HomeworkStatus.AI_GRADING_FAILED -> "批阅失败"
    HomeworkStatus.COMPLETED -> "已完成"
}
fun actionName(value: HomeworkStatus): String = when(value) {
    HomeworkStatus.PENDING_SUBMIT -> "去作答"
    HomeworkStatus.OVERDUE -> "重新提交"
    else -> "查看详情"
}

fun deadlineIsUrgent(status: HomeworkStatus, overdue: Boolean): Boolean = overdue &&
    (status == HomeworkStatus.PENDING_SUBMIT || status == HomeworkStatus.OVERDUE)

@Composable
private fun HomeworkFeed(state: HomeUiState.Success, refresh: () -> Unit, more: () -> Unit, open: (HomeworkUiModel) -> Unit) {
    val scroll = rememberLazyListState()
    val latest by rememberUpdatedState(state)
    val requestMore by rememberUpdatedState(more)
    LaunchedEffect(state.getSelectedSubjectId(), state.getSelectedFilter()) { scroll.scrollToItem(0) }
    LaunchedEffect(scroll) {
        snapshotFlow {
            latest.getHasMore() && latest.getLoadMoreState() is LoadMoreState.Idle &&
                scroll.layoutInfo.visibleItemsInfo.lastOrNull()?.index?.let { it >= scroll.layoutInfo.totalItemsCount - 3 } == true
        }.distinctUntilChanged().collect { if (it) requestMore() }
    }
    PullToRefreshBox(isRefreshing = state.isRefreshing(), onRefresh = refresh, modifier = Modifier.fillMaxSize()) {
        LazyColumn(state = scroll, modifier = Modifier.fillMaxSize(), contentPadding = PaddingValues(start = 24.dp, end = 24.dp, top = 12.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            val task = state.getHomeTaskState()
            if (state.getSelectedSubjectId() == null && task != null && !task.getStateDesc().isNullOrBlank()) {
                item(key = "summary") {
                    Card(Modifier.widthIn(max = 1080.dp).fillMaxWidth(), shape = MaterialTheme.shapes.extraLarge,
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer,
                            contentColor = MaterialTheme.colorScheme.onPrimaryContainer)) {
                        Row(Modifier.padding(24.dp), horizontalArrangement = Arrangement.spacedBy(20.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(if (task.getKind() == HomeTaskStateKind.ALL_FINISHED) Icons.Filled.TaskAlt else Icons.AutoMirrored.Filled.MenuBook, null, Modifier.size(36.dp))
                            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text(if (task.getKind() == HomeTaskStateKind.ALL_FINISHED) "任务已完成" else "学习进度",
                                    style = MaterialTheme.typography.titleLarge)
                                Text(task.getStateDesc(), style = MaterialTheme.typography.bodyLarge)
                            }
                        }
                    }
                }
            }
            item(key = "list-title") {
                Row(Modifier.widthIn(max = 1080.dp).fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(filterName(state.getSelectedFilter()), style = MaterialTheme.typography.titleMedium)
                    Text("已加载 ${state.getHomeworks().size} 份", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            if (state.getHomeworks().isEmpty()) item(key = "empty") {
                Column(Modifier.fillMaxWidth().padding(vertical = 60.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Icon(Icons.AutoMirrored.Filled.MenuBook, null, Modifier.size(48.dp), tint = MaterialTheme.colorScheme.primary)
                    Text(if (state.getSelectedFilter() == null) "这里暂时没有作业" else "没有${filterName(state.getSelectedFilter())}的作业", style = MaterialTheme.typography.titleLarge)
                    TextButton(onClick = refresh) { Text("刷新看看") }
                }
            }
            val subjects = state.getSubjectTabs().filter { it.getId() != null }.associate { it.getId() to it.getLabel() }
            items(state.getHomeworks(), key = { it.getId() }) { work -> HomeworkCard(work, subjects[work.getSubjectId()].orEmpty(), open) }
            if (state.getLoadMoreState() is LoadMoreState.Loading) item(key = "loading-more") {
                CircularProgressIndicator(Modifier.padding(16.dp).size(24.dp), strokeWidth = 2.dp)
            } else if (state.getLoadMoreState() is LoadMoreState.Error) item(key = "retry-more") {
                TextButton(onClick = more) { Text((state.getLoadMoreState() as LoadMoreState.Error).getMessage().ifBlank { "加载失败，点击重试" }) }
            } else if (state.getHasMore()) item(key = "load-more") { TextButton(onClick = more) { Text("加载更多") } }
        }
    }
}

@Composable
private fun HomeworkCard(work: HomeworkUiModel, subject: String, open: (HomeworkUiModel) -> Unit) {
    Card(onClick = { open(work) }, modifier = Modifier.widthIn(max = 1080.dp).fillMaxWidth(), shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLowest)) {
        BoxWithConstraints(Modifier.fillMaxWidth().padding(16.dp)) {
            val small = maxWidth < 600.dp
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Surface(Modifier.size(44.dp), shape = MaterialTheme.shapes.medium,
                        color = MaterialTheme.colorScheme.secondaryContainer, contentColor = MaterialTheme.colorScheme.onSecondaryContainer) {
                        Box(contentAlignment = Alignment.Center) { Icon(subjectGraphic(subject), null) }
                    }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(work.getTitle(), style = MaterialTheme.typography.titleLarge, maxLines = 2, overflow = TextOverflow.Ellipsis)
                        Text("${work.getDeadlineLabel()}  ·  共 ${work.getQuestionCount()} 题", style = MaterialTheme.typography.bodyMedium,
                            color = if (deadlineIsUrgent(work.getStatus(), work.isOverdue())) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    if (!small) WorkActions(work, open)
                }
                if (small) Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    StatusLabel(work.getStatus()); Action(work, open)
                }
            }
        }
    }
}
@Composable private fun WorkActions(work: HomeworkUiModel, open: (HomeworkUiModel) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) { StatusLabel(work.getStatus()); Action(work, open) }
}
@Composable private fun StatusLabel(status: HomeworkStatus) {
    val colors = MaterialTheme.colorScheme
    val pair = when(status) {
        HomeworkStatus.AI_GRADING_FAILED -> colors.errorContainer to colors.onErrorContainer
        HomeworkStatus.PENDING_SUBMIT, HomeworkStatus.OVERDUE -> colors.primaryContainer to colors.onPrimaryContainer
        HomeworkStatus.PENDING_CORRECTION -> colors.secondaryContainer to colors.onSecondaryContainer
        else -> colors.surfaceContainerHigh to colors.onSurfaceVariant
    }
    Surface(shape = MaterialTheme.shapes.small, color = pair.first, contentColor = pair.second) {
        Text(statusName(status), Modifier.padding(horizontal = 10.dp, vertical = 5.dp), style = MaterialTheme.typography.labelMedium)
    }
}
@Composable private fun Action(work: HomeworkUiModel, open: (HomeworkUiModel) -> Unit) {
    val context = LocalContext.current
    val failed = work.getStatus() == HomeworkStatus.AI_GRADING_FAILED
    val primary = work.getStatus() == HomeworkStatus.PENDING_SUBMIT || work.getStatus() == HomeworkStatus.OVERDUE || failed
    if (work.getStatus() == HomeworkStatus.GRADING) Column(horizontalAlignment = Alignment.End) {
        TextButton(onClick = { PendingEdits.request(work, context); open(work) }, shapes = ButtonDefaults.shapes(), modifier = Modifier.heightIn(min = 48.dp)) { Text("修改答案") }
        TextButton(onClick = { open(work) }, shapes = ButtonDefaults.shapes(), modifier = Modifier.heightIn(min = 48.dp)) { Text("查看详情") }
    } else if (primary) Button(onClick = { open(work) }, shapes = ButtonDefaults.shapes(), modifier = Modifier.heightIn(min = 48.dp).widthIn(min = 96.dp)) {
        Text(if (failed) "重试批阅" else actionName(work.getStatus()))
    } else TextButton(onClick = { open(work) }, shapes = ButtonDefaults.shapes(), modifier = Modifier.heightIn(min = 48.dp)) {
        Text(actionName(work.getStatus())); Spacer(Modifier.width(4.dp)); Icon(Icons.Filled.ChevronRight, null, Modifier.size(18.dp))
    }
}
