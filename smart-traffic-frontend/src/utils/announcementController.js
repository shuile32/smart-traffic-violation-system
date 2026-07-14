export function createAnnouncementState() {
  return {
    popoverVisible: false,
    loading: false,
    announcements: [],
    detailVisible: false,
    detailLoading: false,
    selectedAnnouncement: null
  }
}

export function createAnnouncementController({
  state,
  fetchAnnouncements,
  fetchAnnouncement
}) {
  async function loadAnnouncements() {
    state.loading = true
    try {
      const response = await fetchAnnouncements({ page: 1, page_size: 5 })
      state.announcements = response.data.items ?? []
    } catch {
      state.announcements = []
    } finally {
      state.loading = false
    }
  }

  async function selectAnnouncement(id) {
    state.popoverVisible = false
    state.selectedAnnouncement = null
    state.detailVisible = true
    state.detailLoading = true
    try {
      const response = await fetchAnnouncement(id)
      state.selectedAnnouncement = response.data
    } catch {
      state.detailVisible = false
    } finally {
      state.detailLoading = false
    }
  }

  return { loadAnnouncements, selectAnnouncement }
}
