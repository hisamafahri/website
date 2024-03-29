import rss from "@astrojs/rss";
import { getCollection } from "astro:content";

export async function GET(context) {
  const posts = await getCollection("blog");
  return rss({
    title: "Hisam's Journals",
    description: "My thoughts, experiences, and discoveries",
    site: context.site,
    items: posts.map((post) => ({
      ...post.data,
      link: `/journals/${post.slug}/`,
    })),
  });
}
