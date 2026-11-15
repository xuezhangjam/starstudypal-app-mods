
import java.util.*;
import com.hailiang.workcloud.student.data.enums.*;
import com.hailiang.workcloud.student.data.model.*;
import com.hailiang.workcloud.student.data.repository.*;
import com.hailiang.workcloud.student.shareui.work.*;
import com.hailiang.workcloud.student.shareui.work.select.*;
import com.hailiang.workcloud.student.shareui.work.photofile.*;
import com.hailiang.workcloud.student.shareui.home.*;
import com.hailiang.workcloud.student.auth.*;
import kotlinx.coroutines.flow.*;
import kotlin.coroutines.Continuation;
public class Fixture {
 public static class B extends ReviewBlank {
  public String answer="A",teacher="",teacherInk="";public CheckMark mark=CheckMark.PENDING,original=CheckMark.PENDING,teacherMark=CheckMark.PENDING;public ReviewCorrectionStatus correction=ReviewCorrectionStatus.NONE;
  public CheckMark getCheckMark(){return mark;}public CheckMark getOriginalCheckMark(){return original;}public CheckMark getTeacherCorrectMark(){return teacherMark;}public ReviewCorrectionStatus getCorrection(){return correction;}
  public String getTeacherAnswerCheckDetail(){return teacher;}public String getTeacherCorrectionStrokes(){return teacherInk;}public int getIndex(){return 1;}public String getMyAnswer(){return answer;}public List<String> getStudentAnswerPicList(){return Collections.emptyList();}
 }
 public static class WQ extends WorkQuestion {public long getBigQuestionId(){return 42;}public long getSubQuestionId(){return 0;}}
 public static class Q extends ReviewQuestion {
  public B blank=new B();public boolean empty;public WorkQuestion getSource(){return new WQ();}public List<ReviewBlank> getBlanks(){return empty?Collections.emptyList():Collections.singletonList(blank);}public List<ReviewSubQuestion> getSubQuestions(){return Collections.emptyList();}
 }
 public static class WT extends WorkTask {public long getId(){return 7;}public long getSchoolworkId(){return 7;}}
 public static class RT extends ReviewTask {
  public Q q=new Q();public WorkType type=WorkType.SELECT_QUESTION;public boolean finished,ai,teacher;public long state=70;
  public WorkType getWorkType(){return type;}public boolean getTeacherReviewFinished(){return finished;}public boolean getAiGrading(){return ai;}public boolean getHasTeacherMark(){return teacher;}
  public List<MaterialGroupCheck> getMaterialGroupChecks(){return Collections.emptyList();}public List<ReviewAiQuestion> getAiQuestions(){return Collections.emptyList();}public List<ReviewQuestion> getQuestions(){return Collections.singletonList(q);}public WorkTask getWorkTask(){return new WT();}public long getSchoolworkId(){return 7;}public long getSchoolworkStateId(){return state;}
  public String toString(){return "task="+state+";"+q.blank.answer+";"+q.blank.mark+";"+finished+";"+type;}
 }
 public static class WG extends WorkGroup {public long id=1;public long getId(){return id;}public List<WorkTask> getTasks(){return Collections.singletonList(new WT());}}
 public static class RW extends ReviewWork {public WG group=new WG();public RT task=new RT();public WorkGroup getWorkGroup(){return group;}public List<ReviewTask> getTasks(){return Collections.singletonList(task);}}
 public static class QA extends QuestionAnswer {
  public long group=1,work=7;public String answer="A";public long getQuestionId(){return 42;}public long getSubQuestionId(){return 0;}public int getIdx(){return 1;}public long getWorkGroupId(){return group;}public long getWorkId(){return work;}public String getAnswer(){return answer;}public String getStrokes(){return "";}public String getStrokesImg(){return "";}public List<String> getImagePaths(){return Collections.emptyList();}
 }
 public static class WS extends WorkStatus {public List<QuestionAnswer> answers=new ArrayList<QuestionAnswer>();public List<QuestionAnswer> getQuestionAnswers(){return answers;}}
 public static class H extends AnswerQuestionWorkHandler {public boolean submitted=true;public WS status=new WS();public H(){status.answers.add(new QA());}public WorkStatus getStatus(){return status;}public void modBeginRevision(){submitted=false;}}
 public static class PH extends PhotoFileWorkHandler {public boolean submitted=true,photos=true;public boolean getHasPhotoItems(){return photos;}public boolean getHasWritingAnswers(){return false;}public void modBeginRevision(){submitted=false;}}
 public static class Repo extends KtorWorkAnswerRepository {
  public RW work=new RW();public int reads,posts;public boolean fail,pauseReview,pauseOriginal;public WorkGroupSubmitRequest received;public Runnable onRead;public Continuation reviewContinuation,originalContinuation;
  public Object getReviewWorkDetail(long group,Continuation<? super ReviewWork> c){reads++;if(onRead!=null)onRead.run();if(pauseReview){reviewContinuation=c;return kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();}return work;}
  public Object modSubmitWorkGroupOriginal(WorkGroupSubmitRequest r,Continuation<? super kotlin.Unit> c){posts++;received=r;if(fail)throw new IllegalStateException("native server failure");if(pauseOriginal){originalContinuation=c;return kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();}return kotlin.Unit.INSTANCE;}
 }
 public static class Auth implements AuthSessionProvider {public AuthSession account=new AuthSession();public AuthSession current(){return account;}}
 public static class Success extends WorkAnswerUiState.Success {public WG group=new WG();public WorkGroup getWorkGroup(){return group;}}
 public static class VM extends WorkAnswerViewModel {
  public Repo repo=new Repo();public H handler=new H();public Map<Long,WorkHandler> handlers=new HashMap<Long,WorkHandler>();public MutableStateFlow<WorkAnswerUiState> flow=StateFlowKt.MutableStateFlow(new Success());public int refreshed,selected=-1;
  public VM(){handlers.put(7L,handler);}public long modRevisionGroupId(){return 1;}public WorkAnswerRepository modRevisionRepository(){return repo;}public Map<Long,WorkHandler> modRevisionHandlers(){return handlers;}public void modRevisionRefresh(){refreshed++;}public void selectTask(int i){selected=i;}public StateFlow<WorkAnswerUiState> getUiState(){return flow;}
 }
 public static class Home extends HomeworkUiModel {public long getSchoolworkGroupId(){return 1;}public HomeworkStatus getStatus(){return HomeworkStatus.GRADING;}}
 public static class Sub extends SubSchoolworkSubmit {public long state=70;public long getSchoolworkId(){return 7;}public long getSchoolworkStateId(){return state;}}
 public static class Request extends WorkGroupSubmitRequest {public Sub sub=new Sub();public long getSchoolworkGroupId(){return 1;}public List<SubSchoolworkSubmit> getSubSchoolworkList(){return Collections.singletonList(sub);}}
}
