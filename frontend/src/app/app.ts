import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ChangeDetectorRef, Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

type Status = 'idle' | 'loading' | 'ready' | 'error';

interface Mentor {
  id: number;
  name: string;
  field: string;
  description: string;
  research_area?: string;
  photo?: string;
  workshop_title?: string;
  pending_requests?: number;
  total_requests?: number;
}

interface Project {
  id: number;
  title: string;
  category: string;
  description: string;
  team_size?: number;
  mentor_id?: number;
  mentor_name?: string;
  accepted?: number;
  capacity?: number;
  available?: number;
  is_full?: boolean;
  members?: RequestItem[];
}

interface RequestItem {
  id: number;
  request_type: 'mentor' | 'project';
  status: string;
  mentor_id?: number;
  mentor_name?: string;
  project_id?: number;
  project_title?: string;
  student_name: string;
  email: string;
  role?: string;
  faculty?: string;
  skills?: string;
  availability?: string;
  interest?: string;
  intro?: string;
  message?: string;
}

interface StudentSession {
  email: string;
  student_name: string;
  pending: number;
  accepted: number;
  requests: RequestItem[];
}

interface MentorSession {
  mentor: Mentor;
  requests: RequestItem[];
  projects: Project[];
}

interface ApiResponse {
  status: 'success' | 'error';
  message?: string;
  [key: string]: unknown;
}

interface ChatMessage {
  from: 'student' | 'assistant';
  text: string;
}

type AuthModal =
  | 'student-login'
  | 'student-register'
  | 'mentor-login'
  | 'mentor-register'
  | 'admin-login'
  | null;

interface AdminStudent {
  id: number;
  name: string;
  email: string;
  photo_url?: string;
  created_at: string;
}

interface AdminData {
  students: AdminStudent[];
  pending: Mentor[];
  approved: Mentor[];
  rejected: Mentor[];
}

@Component({
  selector: 'app-root',
  imports: [CommonModule, FormsModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  mentors = signal<Mentor[]>([]);
  projects = signal<Project[]>([]);
  status = signal<Status>('idle');
  currentPage = signal('home');
  notice = signal('');
  student = signal<StudentSession | null>(null);
  mentorSession = signal<MentorSession | null>(null);
  chatMessages = signal<ChatMessage[]>([
    {
      from: 'assistant',
      text: 'Ask me how to find a mentor, submit a project, choose a STEM area, or understand the portal flow.'
    }
  ]);
  chatBusy = signal(false);
  adminLoggedIn = signal(false);
  adminData = signal<AdminData | null>(null);
  authModal: AuthModal = null;

  studentLogin = { student_name: '', email: '', password: '' };
  mentorRequest = { mentor_id: '', interest: '', message: '' };
  projectRequest = { project_id: '', mentor_id: '', project_title: '', role: '', faculty: '', skills: '', availability: '', intro: '', message: '' };
  mentorLogin = { email: '', access_code: '' };
  mentorRegistration = {
    name: '',
    field: '',
    description: '',
    research_area: '',
    email: '',
    access_code: '',
    workshop_title: '',
    workshop_description: ''
  };
  newProject = { title: '', category: '', description: '', team_size: 4 };
  chatInput = '';
  adminPassword = '';
  portalTab: 'mentors' | 'projects' | 'workspace' = 'mentors';
  adminTab: 'students' | 'pending' | 'approved' | 'rejected' = 'pending';
  mentorAuthMode: 'login' | 'register' = 'login';

  // Thought bubble cycling
  thoughtMessages = [
    'Thinking... start with a mentor, choose a STEM track, then turn your idea into a real project.',
    'Need a plan? Pick AI, robotics, IoT, software, or data science and I will guide your next step.',
    'Tip: ask STEM Bot about mentors, projects, project roles, or how to submit a strong request.',
    'Great projects begin with one clear problem. What campus challenge would you solve first?',
    'Welcome to the STEM Portal! Ready to build something awesome? 🚀',
    'Find a mentor and kickstart your STEM journey! 🧪',
    'Got an idea? Join a project team today! 💡',
    'AI, IoT, Robotics — explore all STEM fields here! 🤖',
    'Register as a mentor and inspire the next generation! ⭐',
    'Need help? Ask the STEM Bot anything! 💬',
    'MMU Cyberjaya & Melaka — two campuses, one mission! 🎓',
  ];
  thoughtIndex = 0;
  thoughtFading = false;
  private thoughtInterval: ReturnType<typeof setInterval> | null = null;

  // Floating chatbot
  private readonly chatLauncherSize = 68;
  chatOpen = false;
  chatPos = this.clampPosition({ x: window.innerWidth - 400, y: window.innerHeight - 540 }, this.chatWindowWidth(), this.chatWindowHeight());
  chatLauncherPos = this.clampPosition({ x: window.innerWidth - 92, y: window.innerHeight - 92 }, this.chatLauncherSize, this.chatLauncherSize);
  chatDragging = false;
  launcherDragging = false;

  acceptedMentorCount = computed(() =>
    (this.student()?.requests ?? []).filter((request) => request.request_type === 'mentor' && request.status === 'accepted').length
  );

  activeRequests = computed(() =>
    (this.student()?.requests ?? []).filter((request) => !['withdrawn', 'removed', 'project_deleted'].includes(request.status))
  );

  ngOnInit(): void {
    this.setCurrentPage(this.router.url);
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.setCurrentPage(event.urlAfterRedirects);
      }
    });
    this.refreshCatalog();
    this.refreshStudentSession(false);
    this.refreshMentorSession(false);
    this.startThoughtCycle();
  }

  ngOnDestroy(): void {
    if (this.thoughtInterval) {
      clearInterval(this.thoughtInterval);
    }
  }

  private startThoughtCycle(): void {
    this.thoughtInterval = setInterval(() => {
      this.thoughtFading = true;
      this.cdr.detectChanges();
      setTimeout(() => {
        this.thoughtIndex = (this.thoughtIndex + 1) % this.thoughtMessages.length;
        this.thoughtFading = false;
        this.cdr.detectChanges();
      }, 500);
    }, 4000);
  }

  useMascotFallback(event: Event): void {
    const image = event.target as HTMLImageElement;
    const fallbackIndex = Number(image.dataset['fallbackIndex'] ?? '0');
    const fallbacks = ['/static/img/ebee-home.png', '/assets/mmu-ebee.png', '/static/img/mmu-ebee.png'];

    if (fallbackIndex < fallbacks.length) {
      image.dataset['fallbackIndex'] = String(fallbackIndex + 1);
      image.src = fallbacks[fallbackIndex];
      return;
    }

    image.style.display = 'none';
  }

  toggleChat(): void {
    this.chatOpen = !this.chatOpen;
    if (this.chatOpen) {
      this.chatPos = this.clampPosition(this.chatPos, this.chatWindowWidth(), this.chatWindowHeight());
    }
  }

  openChatFromLauncher(event: MouseEvent): void {
    if (this.launcherMoved) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }

    this.chatPos = this.clampPosition(
      {
        x: this.chatLauncherPos.x - this.chatWindowWidth() + this.chatLauncherSize,
        y: this.chatLauncherPos.y - this.chatWindowHeight() - 14
      },
      this.chatWindowWidth(),
      this.chatWindowHeight()
    );
    this.chatOpen = true;
  }

  private setCurrentPage(url: string): void {
    const page = url.split('?')[0].replace('/', '') || 'home';
    this.currentPage.set(page);
  }

  openAuthModal(modal: Exclude<AuthModal, null>): void {
    this.authModal = modal;
  }

  closeAuthModal(): void {
    this.authModal = null;
  }

  refreshCatalog(): void {
    this.status.set('loading');
    this.http.get<Mentor[]>('/mentors').subscribe({
      next: (mentors) => {
        this.mentors.set(mentors);
        this.http.get<Project[]>('/projects').subscribe({
          next: (projects) => {
            this.projects.set(projects);
            this.status.set('ready');
          },
          error: () => this.status.set('error')
        });
      },
      error: () => this.status.set('error')
    });
  }

  loginStudent(): void {
    this.notice.set('Signing in...');
    this.http.post<StudentSession & ApiResponse>('/api/student/login', { ...this.studentLogin, mode: 'login' }).subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.student.set(response);
          this.closeAuthModal();
          this.portalTab = 'workspace';
          this.notice.set('Student workspace ready.');
        } else {
          this.notice.set(response.message ?? 'Student login failed.');
        }
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Student login failed.')
    });
  }

  registerStudent(): void {
    this.notice.set('Creating student account...');
    this.http.post<StudentSession & ApiResponse>('/api/student/login', { ...this.studentLogin, mode: 'register' }).subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.student.set(response);
          this.closeAuthModal();
          this.portalTab = 'workspace';
          this.notice.set('Student account ready.');
        } else {
          this.notice.set(response.message ?? 'Student registration failed.');
        }
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Student registration failed.')
    });
  }

  refreshStudentSession(showErrors = true): void {
    this.http.get<StudentSession & ApiResponse>('/api/student/requests').subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.student.set(response);
        }
      },
      error: () => {
        if (showErrors) {
          this.notice.set('Sign in as a student first.');
        }
      }
    });
  }

  sendMentorRequest(): void {
    this.notice.set('Sending mentor request...');
    this.http.post<ApiResponse>('/api/join_mentor', this.mentorRequest).subscribe({
      next: (response) => {
        this.notice.set(response.message ?? 'Mentor request sent.');
        this.mentorRequest = { mentor_id: '', interest: '', message: '' };
        this.refreshStudentSession();
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not send mentor request.')
    });
  }

  sendProjectRequest(): void {
    const selectedProject = this.projects().find((project) => String(project.id) === String(this.projectRequest.project_id));
    const payload = {
      ...this.projectRequest,
      project_title: this.projectRequest.project_title || selectedProject?.title || ''
    };
    this.notice.set('Sending project request...');
    this.http.post<ApiResponse>('/api/join_project', payload).subscribe({
      next: (response) => {
        this.notice.set(response.message ?? 'Project request sent.');
        this.projectRequest = { project_id: '', mentor_id: '', project_title: '', role: '', faculty: '', skills: '', availability: '', intro: '', message: '' };
        this.refreshStudentSession();
        this.refreshCatalog();
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not send project request.')
    });
  }

  withdrawRequest(request: RequestItem): void {
    this.http.post<ApiResponse>(`/api/student/withdraw/${request.id}`, {}).subscribe({
      next: () => {
        this.notice.set('Request withdrawn.');
        this.refreshStudentSession();
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not withdraw request.')
    });
  }

  registerMentor(): void {
    this.notice.set('Submitting mentor registration...');
    this.http.post<ApiResponse>('/api/add_mentor', this.mentorRegistration).subscribe({
      next: (response) => {
        this.notice.set(response.message ?? 'Mentor submitted for admin approval.');
        this.mentorRegistration = { name: '', field: '', description: '', research_area: '', email: '', access_code: '', workshop_title: '', workshop_description: '' };
        this.closeAuthModal();
        this.mentorAuthMode = 'login';
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not register mentor.')
    });
  }

  loginMentor(): void {
    this.notice.set('Signing in mentor...');
    this.http.post<MentorSession & ApiResponse>('/api/mentor/login', this.mentorLogin).subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.mentorSession.set({ mentor: response.mentor, requests: response.requests ?? [], projects: [] });
          this.notice.set('Mentor workspace ready.');
          this.closeAuthModal();
          this.refreshMentorSession();
        }
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Mentor login failed.')
    });
  }

  refreshMentorSession(showErrors = true): void {
    this.http.get<MentorSession & ApiResponse>('/api/mentor/requests').subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.mentorSession.set({ mentor: response.mentor, requests: response.requests ?? [], projects: response.projects ?? [] });
        }
      },
      error: () => {
        if (showErrors) {
          this.notice.set('Sign in as an approved mentor first.');
        }
      }
    });
  }

  decideRequest(request: RequestItem, action: 'accepted' | 'rejected'): void {
    this.http.post<ApiResponse>(`/api/mentor/requests/${request.id}/decision`, { action }).subscribe({
      next: () => {
        this.notice.set(`Request ${action}.`);
        this.refreshMentorSession();
        this.refreshCatalog();
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not update request.')
    });
  }

  createMentorProject(): void {
    this.http.post<ApiResponse>('/api/mentor/projects', this.newProject).subscribe({
      next: () => {
        this.notice.set('Project created.');
        this.newProject = { title: '', category: '', description: '', team_size: 4 };
        this.refreshMentorSession();
        this.refreshCatalog();
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not create project.')
    });
  }

  askChatbot(): void {
    const question = this.chatInput.trim();
    if (!question) {
      return;
    }
    this.chatMessages.update((messages) => [...messages, { from: 'student', text: question }]);
    this.chatInput = '';
    this.chatBusy.set(true);
    this.http.post<{ reply: string }>('/api/chatbot', { message: question, student: this.student(), projects: this.projects() }).subscribe({
      next: (response) => {
        this.chatMessages.update((messages) => [...messages, { from: 'assistant', text: response.reply }]);
        this.chatBusy.set(false);
      },
      error: () => {
        this.chatMessages.update((messages) => [...messages, { from: 'assistant', text: 'I could not answer just now. Try asking about mentors, projects, requests, or STEM study planning.' }]);
        this.chatBusy.set(false);
      }
    });
  }

  initials(name = 'MMU'): string {
    return name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('');
  }

  quickMentorRequest(mentor: Mentor): void {
    this.mentorRequest.mentor_id = String(mentor.id);
    this.mentorRequest.interest = mentor.field || '';
    this.mentorRequest.message = `I'd like to connect with ${mentor.name} for mentorship.`;
    this.sendMentorRequest();
  }

  quickProjectRequest(project: Project): void {
    this.projectRequest.project_id = String(project.id);
    this.projectRequest.project_title = project.title;
    this.projectRequest.mentor_id = String(project.mentor_id || '');
    this.projectRequest.intro = `Requesting to join ${project.title}.`;
    this.sendProjectRequest();
  }

  loginAdmin(): void {
    this.notice.set('Authenticating admin...');
    this.http.post<ApiResponse>('/api/admin/login', { password: this.adminPassword }).subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.adminLoggedIn.set(true);
          this.adminPassword = '';
          this.notice.set('Admin dashboard ready.');
          this.closeAuthModal();
          this.refreshAdminData();
        } else {
          this.notice.set(response.message ?? 'Admin login failed.');
        }
      },
      error: (error) => this.notice.set(error.error?.message ?? 'Invalid admin password.')
    });
  }

  refreshAdminData(): void {
    this.http.get<AdminData & ApiResponse>('/api/admin/data').subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.adminData.set(response);
        }
      },
      error: () => this.adminLoggedIn.set(false)
    });
  }

  adminApproveMentor(mentorId: number): void {
    this.http.post<ApiResponse>(`/api/admin/mentors/${mentorId}/approve`, {}).subscribe({
      next: () => { this.notice.set('Mentor approved.'); this.refreshAdminData(); this.refreshCatalog(); },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not approve mentor.')
    });
  }

  adminRejectMentor(mentorId: number): void {
    this.http.post<ApiResponse>(`/api/admin/mentors/${mentorId}/reject`, {}).subscribe({
      next: () => { this.notice.set('Mentor rejected.'); this.refreshAdminData(); },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not reject mentor.')
    });
  }

  adminDeleteMentor(mentorId: number): void {
    this.http.post<ApiResponse>(`/api/admin/mentors/${mentorId}/delete`, {}).subscribe({
      next: () => { this.notice.set('Mentor removed.'); this.refreshAdminData(); this.refreshCatalog(); },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not delete mentor.')
    });
  }

  adminDeleteStudent(studentId: number): void {
    this.http.post<ApiResponse>(`/api/admin/students/${studentId}/delete`, {}).subscribe({
      next: () => { this.notice.set('Student removed.'); this.refreshAdminData(); },
      error: (error) => this.notice.set(error.error?.message ?? 'Could not delete student.')
    });
  }

  logoutAdmin(): void {
    this.http.post<ApiResponse>('/api/admin/logout', {}).subscribe({
      next: () => { this.adminLoggedIn.set(false); this.adminData.set(null); this.notice.set('Admin logged out.'); },
      error: () => { this.adminLoggedIn.set(false); this.adminData.set(null); }
    });
  }

  // --- Draggable chat window and launcher ---
  private dragging = false;
  private launcherMoved = false;
  private dragOffset = { x: 0, y: 0 };

  startDrag(event: PointerEvent): void {
    if (event.button !== 0) {
      return;
    }

    this.dragging = true;
    this.chatDragging = true;
    this.dragOffset = {
      x: event.clientX - this.chatPos.x,
      y: event.clientY - this.chatPos.y
    };

    const onMove = (e: PointerEvent) => {
      if (!this.dragging) {
        return;
      }
      this.chatPos = this.clampPosition(
        { x: e.clientX - this.dragOffset.x, y: e.clientY - this.dragOffset.y },
        this.chatWindowWidth(),
        this.chatWindowHeight()
      );
      this.cdr.detectChanges();
    };

    const onUp = () => {
      this.dragging = false;
      this.chatDragging = false;
      this.cdr.detectChanges();
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
    };

    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp, { once: true });
    event.preventDefault();
  }

  startLauncherDrag(event: PointerEvent): void {
    if (event.button !== 0) {
      return;
    }

    this.launcherDragging = true;
    this.launcherMoved = false;
    const start = { x: event.clientX, y: event.clientY };
    const offset = {
      x: event.clientX - this.chatLauncherPos.x,
      y: event.clientY - this.chatLauncherPos.y
    };

    const onMove = (e: PointerEvent) => {
      const movedX = Math.abs(e.clientX - start.x);
      const movedY = Math.abs(e.clientY - start.y);
      if (movedX > 4 || movedY > 4) {
        this.launcherMoved = true;
      }
      this.chatLauncherPos = this.clampPosition(
        { x: e.clientX - offset.x, y: e.clientY - offset.y },
        this.chatLauncherSize,
        this.chatLauncherSize
      );
      this.cdr.detectChanges();
    };

    const onUp = () => {
      this.launcherDragging = false;
      this.cdr.detectChanges();
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      window.setTimeout(() => {
        this.launcherMoved = false;
        this.cdr.detectChanges();
      });
    };

    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp, { once: true });
    event.preventDefault();
  }

  private chatWindowWidth(): number {
    return Math.min(370, Math.max(280, window.innerWidth - 24));
  }

  private chatWindowHeight(): number {
    return Math.min(460, Math.max(340, window.innerHeight - 24));
  }

  private clampPosition(position: { x: number; y: number }, width: number, height: number): { x: number; y: number } {
    const padding = 12;
    const maxX = Math.max(padding, window.innerWidth - width - padding);
    const maxY = Math.max(padding, window.innerHeight - height - padding);

    return {
      x: Math.max(padding, Math.min(maxX, position.x)),
      y: Math.max(padding, Math.min(maxY, position.y))
    };
  }
}
