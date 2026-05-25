
function app() {
  return {
    // State
    lang: localStorage.getItem('lang') || 'en',
    isLoggedIn: false,
    loading: false,
    page: 'dashboard',
    mobileMenuOpen: false,
    user: null,
    toasts: [],
    locales: {},

    // Login
    loginForm: { email: '', password: '' },
    loginError: '',

    // Clients
    clients: [],
    clientPagination: { page: 1, limit: 50, total: 0 },
    clientFilters: {
      search: '',
      travel_type: '',
      status: '',
      gender: '',
      travel_date_from: '',
      travel_date_to: ''
    },
    showFilters: false,
    editingClient: null,
    clientForms: [],

    // Travel Types
    travelTypes: [],
    travelTypeModalOpen: false,
    editingTravelType: null,
    travelTypeForm: { code: '', name_en: '', name_fr: '', name_ar: '' },

    // Users
    users: [],
    userModalOpen: false,
    editingUser: null,
    userForm: { full_name: '', email: '', password: '', role: 'agent', preferred_lang: 'en' },

    // Import
    importModalOpen: false,
    importStep: 1,
    importPreview: { validation_id: '', total_rows: 0, valid_rows: 0, errors: [], preview_data: [] },
    importResult: { imported_count: 0, duplicates_skipped: 0 },

    // Export
    exportJobId: null,
    exportPolling: null,

    // Dashboard
    stats: { total: 0, active: 0, byType: [] },

    async initApp() {
      // Auth disabled – auto-login
      this.isLoggedIn = true;
      this.user = { id: 1, email: 'admin@minadoor.com', role: 'admin', full_name: 'Admin', preferred_lang: 'en' };
      await this.loadLocale();
      await this.loadTravelTypes();
      await this.loadClients();
    },

    async loadLocale() {
      try {
        const res = await fetch(`/locales/${this.lang}.json`);
        this.locales = await res.json();
      } catch (e) {
        this.locales = {};
      }
    },

    t(key) {
      return this.locales[key] || key;
    },

    setLang(l) {
      this.lang = l;
      localStorage.setItem('lang', l);
      this.loadLocale();
      document.documentElement.lang = l;
      document.documentElement.dir = l === 'ar' ? 'rtl' : 'ltr';
      if (this.isLoggedIn) {
        this.loadTravelTypes();
        if (this.page === 'clients') this.loadClients();
      }
    },

    pageTitle() {
      return this.t(this.page === 'client-form' ? 'clients' : this.page);
    },

    navigate(p) {
      this.page = p;
      this.mobileMenuOpen = false;
      if (p === 'clients') this.loadClients();
      if (p === 'travel-types') this.loadTravelTypes();
      if (p === 'users') this.loadUsers();
      if (p === 'dashboard') this.loadStats();
      if (p === 'client-form') {
        this.editingClient = null;
        this.clientForms = [this.emptyClientForm()];
      }
    },

    emptyClientForm() {
      return {
        surname: '', given_name: '', father_name: '', mother_name: '',
        passport_number: '', nationality: '', date_of_birth: '',
        passport_issue_date: '', passport_expiry: '', gender: '',
        travel_type_id: '', payment_method: 'cash', travel_date: '', notes: ''
      };
    },

    addClientForm() {
      this.clientForms.push(this.emptyClientForm());
    },

    removeClientForm(idx) {
      this.clientForms.splice(idx, 1);
    },

    async doLogin() {
      this.loading = true;
      this.loginError = '';
      try {
        const res = await fetch('/api/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.loginForm)
        });
        const data = await res.json();
        if (res.ok) {
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          this.isLoggedIn = true;
          await this.initApp();
          this.navigate('dashboard');
        } else {
          this.loginError = data.detail || this.t('auth_failed');
        }
      } catch (e) {
        this.loginError = this.t('error_occurred');
      }
      this.loading = false;
    },

    doLogout() {
      const rt = localStorage.getItem('refresh_token');
      if (rt) {
        fetch('/api/api/v1/auth/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: rt })
        }).catch(() => {});
      }
      this.logout();
    },

    logout() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.isLoggedIn = false;
      this.user = null;
      this.page = 'dashboard';
    },

    api(path, opts = {}) {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Accept-Language': this.lang,
        ...(opts.body && !(opts.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...opts.headers
      };
      return fetch('/api/v1' + path, { ...opts, headers });
    },

    async loadClients() {
      this.loading = true;
      const params = new URLSearchParams();
      params.set('page', this.clientPagination.page);
      params.set('limit', this.clientPagination.limit);
      if (this.clientFilters.search) params.set('search', this.clientFilters.search);
      if (this.clientFilters.travel_type) params.set('travel_type', this.clientFilters.travel_type);
      if (this.clientFilters.status) params.set('status', this.clientFilters.status);
      if (this.clientFilters.gender) params.set('gender', this.clientFilters.gender);
      if (this.clientFilters.travel_date_from) params.set('travel_date_from', this.clientFilters.travel_date_from);
      if (this.clientFilters.travel_date_to) params.set('travel_date_to', this.clientFilters.travel_date_to);

      try {
        const res = await this.api(`/clients?${params}`);
        if (res.ok) {
          const data = await res.json();
          this.clients = data.items;
          this.clientPagination.total = data.total;
        }
      } catch (e) {}
      this.loading = false;
    },

    prevPage() {
      if (this.clientPagination.page > 1) {
        this.clientPagination.page--;
        this.loadClients();
      }
    },

    nextPage() {
      if (this.clientPagination.page * this.clientPagination.limit < this.clientPagination.total) {
        this.clientPagination.page++;
        this.loadClients();
      }
    },

    resetFilters() {
      this.clientFilters = { search: '', travel_type: '', status: '', gender: '', travel_date_from: '', travel_date_to: '' };
      this.clientPagination.page = 1;
      this.loadClients();
    },

    async loadTravelTypes() {
      try {
        const res = await this.api(`/travel-types?lang=${this.lang}`);
        if (res.ok) this.travelTypes = await res.json();
      } catch (e) {}
    },

    async loadUsers() {
      try {
        const res = await this.api('/users');
        if (res.ok) this.users = await res.json();
      } catch (e) {}
    },

    async loadStats() {
      try {
        // Total
        let res = await this.api('/clients?limit=1');
        if (res.ok) {
          const data = await res.json();
          this.stats.total = data.total;
        }
        // Active
        res = await this.api('/clients?status=active&limit=1');
        if (res.ok) {
          const data = await res.json();
          this.stats.active = data.total;
        }
        // By type
        this.stats.byType = [];
        for (const tt of this.travelTypes) {
          res = await this.api(`/clients?travel_type=${tt.code}&limit=1`);
          if (res.ok) {
            const data = await res.json();
            this.stats.byType.push({ code: tt.code, name: tt.name, count: data.total });
          }
        }
      } catch (e) {}
    },

    editClient(c) {
      this.editingClient = c;
      this.clientForms = [{
        surname: c.surname, given_name: c.given_name, father_name: c.father_name,
        mother_name: c.mother_name || '', passport_number: c.passport_number,
        nationality: c.nationality, date_of_birth: c.date_of_birth || '',
        passport_issue_date: c.passport_issue_date || '', passport_expiry: c.passport_expiry || '',
        gender: c.gender || '', travel_type_id: c.travel_type_id,
        payment_method: c.payment_method, travel_date: c.travel_date, notes: c.notes || ''
      }];
      this.navigate('client-form');
    },

    async deleteClient(id) {
      if (!confirm(this.t('confirm_delete'))) return;
      try {
        const res = await this.api(`/clients/${id}`, { method: 'DELETE' });
        if (res.ok) {
          this.showToast(this.t('delete') + ' OK', 'success');
          this.loadClients();
        }
      } catch (e) {}
    },

    async saveClients() {
      this.loading = true;
      try {
        if (this.editingClient) {
          const form = this.clientForms[0];
          const res = await this.api(`/clients/${this.editingClient.id}`, {
            method: 'PATCH',
            body: JSON.stringify(form)
          });
          if (res.ok) {
            this.showToast(this.t('save') + ' OK', 'success');
            this.navigate('clients');
          } else {
            const err = await res.json();
            this.showToast(err.detail || this.t('error_occurred'), 'error');
          }
        } else {
          // Batch create
          let ok = 0;
          for (const form of this.clientForms) {
            const res = await this.api('/clients', {
              method: 'POST',
              body: JSON.stringify(form)
            });
            if (res.ok) ok++;
          }
          this.showToast(`${ok}/${this.clientForms.length} ${this.t('save')} OK`, 'success');
          this.navigate('clients');
        }
      } catch (e) {
        this.showToast(this.t('error_occurred'), 'error');
      }
      this.loading = false;
    },

    // Import
    openImportModal() {
      this.importModalOpen = true;
      this.importStep = 1;
      this.importPreview = { validation_id: '', total_rows: 0, valid_rows: 0, errors: [], preview_data: [] };
    },

    handleFileDrop(e) {
      e.preventDefault();
      const files = e.dataTransfer.files;
      if (files.length) this.uploadImportFile(files[0]);
    },

    handleFileSelect(e) {
      const files = e.target.files;
      if (files.length) this.uploadImportFile(files[0]);
    },

    async uploadImportFile(file) {
      this.loading = true;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await this.api('/clients/import/preview', { method: 'POST', body: formData });
        if (res.ok) {
          this.importPreview = await res.json();
          this.importStep = 2;
        } else {
          const err = await res.json();
          this.showToast(err.detail || this.t('import_failed'), 'error');
        }
      } catch (e) {
        this.showToast(this.t('error_occurred'), 'error');
      }
      this.loading = false;
    },

    async confirmImport() {
      this.loading = true;
      try {
        // Build corrected rows from preview_data (user may have edited inline in a real app)
        // Here we just send the valid preview rows
        const rows = this.importPreview.preview_data;
        // In a real app, user edits rows inline; here we send preview
        const res = await this.api('/clients/import/confirm', {
          method: 'POST',
          body: JSON.stringify({ rows })
        });
        if (res.ok) {
          this.importResult = await res.json();
          this.importStep = 3;
        }
      } catch (e) {
        this.showToast(this.t('error_occurred'), 'error');
      }
      this.loading = false;
    },

    // Export
    async doExport(format) {
      this.loading = true;
      try {
        const body = {
          format,
          search: this.clientFilters.search || undefined,
          travel_type: this.clientFilters.travel_type || undefined,
          status: this.clientFilters.status || undefined,
          gender: this.clientFilters.gender || undefined,
          travel_date_from: this.clientFilters.travel_date_from || undefined,
          travel_date_to: this.clientFilters.travel_date_to || undefined,
          header_lang: this.lang
        };
        const res = await this.api('/clients/export', {
          method: 'POST',
          body: JSON.stringify(body)
        });
        if (res.ok) {
          const data = await res.json();
          this.exportJobId = data.job_id;
          this.showToast(this.t('processing') + '...', 'success');
          this.pollExportStatus();
        }
      } catch (e) {}
      this.loading = false;
    },

    pollExportStatus() {
      if (this.exportPolling) clearInterval(this.exportPolling);
      this.exportPolling = setInterval(async () => {
        try {
          const res = await this.api(`/exports/${this.exportJobId}/status`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === 'completed') {
              clearInterval(this.exportPolling);
              this.showToast(this.t('export_ready'), 'success');
              window.open(`/api/api/v1/exports/${this.exportJobId}/download`, '_blank');
            } else if (data.status === 'failed') {
              clearInterval(this.exportPolling);
              this.showToast(this.t('export_failed'), 'error');
            }
          }
        } catch (e) {}
      }, 3000);
    },

    // Travel Types
    openTravelTypeModal(tt = null) {
      this.editingTravelType = tt;
      if (tt) {
        this.travelTypeForm = { code: tt.code, name_en: tt.name_en, name_fr: tt.name_fr, name_ar: tt.name_ar };
      } else {
        this.travelTypeForm = { code: '', name_en: '', name_fr: '', name_ar: '' };
      }
      this.travelTypeModalOpen = true;
    },

    async saveTravelType() {
      try {
        const method = this.editingTravelType ? 'PATCH' : 'POST';
        const path = this.editingTravelType ? `/travel-types/${this.editingTravelType.id}` : '/travel-types';
        const res = await this.api(path, {
          method,
          body: JSON.stringify(this.travelTypeForm)
        });
        if (res.ok) {
          this.travelTypeModalOpen = false;
          this.loadTravelTypes();
          this.showToast(this.t('save') + ' OK', 'success');
        }
      } catch (e) {}
    },

    async deleteTravelType(id) {
      if (!confirm(this.t('confirm_delete'))) return;
      try {
        const res = await this.api(`/travel-types/${id}`, { method: 'DELETE' });
        if (res.ok) {
          this.loadTravelTypes();
          this.showToast(this.t('delete') + ' OK', 'success');
        }
      } catch (e) {}
    },

    // Users
    openUserModal(u = null) {
      this.editingUser = u;
      if (u) {
        this.userForm = { full_name: u.full_name, email: u.email, password: '', role: u.role, preferred_lang: u.preferred_lang };
      } else {
        this.userForm = { full_name: '', email: '', password: '', role: 'agent', preferred_lang: 'en' };
      }
      this.userModalOpen = true;
    },

    async saveUser() {
      try {
        const method = this.editingUser ? 'PATCH' : 'POST';
        const path = this.editingUser ? `/users/${this.editingUser.id}` : '/users';
        const body = { ...this.userForm };
        if (this.editingUser) delete body.password;
        const res = await this.api(path, { method, body: JSON.stringify(body) });
        if (res.ok) {
          this.userModalOpen = false;
          this.loadUsers();
          this.showToast(this.t('save') + ' OK', 'success');
        }
      } catch (e) {}
    },

    async deleteUser(id) {
      if (!confirm(this.t('confirm_delete'))) return;
      try {
        const res = await this.api(`/users/${id}`, { method: 'DELETE' });
        if (res.ok) {
          this.loadUsers();
          this.showToast(this.t('delete') + ' OK', 'success');
        }
      } catch (e) {}
    },

    showToast(message, type = 'success') {
      const id = Date.now();
      this.toasts.push({ id, message, type });
      setTimeout(() => {
        this.toasts = this.toasts.filter(t => t.id !== id);
      }, 4000);
    }
  };
}
// Global sanitizer
function sanitize(dirty) {
    return window.DOMPurify ? DOMPurify.sanitize(dirty) : dirty;
}
