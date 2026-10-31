---
title: The AI Signal 42, memory upgrades and small models
target_duration: 180
words_per_minute: 150
banned_phrases: game changer, mind blowing
---

# Hook
Three labs shipped model updates this week, and none of them were about size. All three were about memory.

# Segment one: context that survives
The first release extends how long a model can hold onto earlier parts of a conversation before it starts losing the thread. In practice that means fewer repeated questions, fewer summaries that quietly drop the detail you cared about, and fewer moments where the assistant forgets the constraint you set ten minutes ago.

For anyone building on top of these APIs, the interesting part is not the new number in the announcement. It is what changes when you stop designing around forgetting. Retrieval stops being a workaround and becomes a design choice. You can keep the whole working set in the window and spend your engineering time on something more useful than summarising the past.

The catch is cost. Every cached token is still a token you pay for, and a long conversation is now a long bill. If you were relying on context growth as a free upgrade, read the pricing page before you ship.

# Segment two: the small models get good
The second release is a smaller model tuned for on device work. It is not trying to win a benchmark. It is trying to fit inside the memory of a phone while still following instructions reliably, which is a very different target than squeezing out another point of accuracy.

That trade is the one to watch this year. A mediocre model that runs locally, instantly and for free beats a great one that waits in a queue [[asset: broll/phone-demo.mp4]]. The latency budget changes what products are even possible. Voice interfaces and autocomplete stop feeling like demos.

The honest limitation is task length. Small models still fall apart when you ask them to hold several instructions at once, so keep the jobs narrow and give them a clear failure path.

# Segment three: what it costs you
The third change is a pricing change, and it is the one that will hit your bill. Long context requests are now metered differently, so a prompt that used to be flat rate scales with how much you feed it. Batch work is cheaper, interactive work is not.

Run your evaluation suite once before you rerun anything at scale. The surprise almost always hides in development runs, not in production traffic, because development is where you paste a whole repository into the prompt and call it a day.

# Close
Memory, size, and price. Pick the one that changes your architecture and ignore the rest for a week. I will be back tomorrow with the papers worth reading and the benchmarks worth distrusting [[asset: broll/outro-card.png]].
