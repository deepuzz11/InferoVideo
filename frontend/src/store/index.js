import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // Active job
  activeJobId: null,
  job: null,
  chapters: [],
  highlights: [],
  summary: null,
  searchResults: [],
  searchQuery: '',
  activeTab: 'chapters',    // chapters | search | highlights | summary
  activeChapter: null,
  videoTime: 0,
  isSearching: false,
  toasts: [],

  setActiveJob:     (id)  => set({ activeJobId: id }),
  setJob:           (job) => set({ job }),
  setChapters:      (c)   => set({ chapters: c }),
  setHighlights:    (h)   => set({ highlights: h }),
  setSummary:       (s)   => set({ summary: s }),
  setSearchResults: (r)   => set({ searchResults: r }),
  setSearchQuery:   (q)   => set({ searchQuery: q }),
  setActiveTab:     (t)   => set({ activeTab: t }),
  setActiveChapter: (c)   => set({ activeChapter: c }),
  setVideoTime:     (t)   => set({ videoTime: t }),
  setIsSearching:   (v)   => set({ isSearching: v }),

  addToast: (msg, type = 'info') => {
    const id = Date.now()
    set(s => ({ toasts: [...s.toasts, { id, msg, type }] }))
    setTimeout(() => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })), 3500)
  },

  reset: () => set({
    activeJobId: null, job: null, chapters: [], highlights: [],
    summary: null, searchResults: [], searchQuery: '', activeChapter: null,
  }),
}))
