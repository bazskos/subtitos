from guessit import guessit

class SubtitleScorer:
    """Evaluates and scores subtitles based on media metadata."""

    PERFECT_SCORE = 100
    MIN_ACCEPTABLE_SCORE = 40  # Source must match at minimum

    @staticmethod
    def calculate_score(media_data: dict, subtitle_filename: str) -> int:
        score = 0
        if not subtitle_filename:
            return score

        sub_data = guessit(subtitle_filename)
        sub_filename_lower = subtitle_filename.lower()
        media_filename_lower = media_data.get("original_filename", "").lower()

        # 1. SOURCE MATCH (+40 points)
        # Most critical for sync - WEB-DL vs BluRay have different timing
        media_source = media_data.get("source")
        sub_source = sub_data.get("source")
        source_matched = False

        if media_source and sub_source and str(media_source).lower() == str(sub_source).lower():
            source_matched = True
        elif media_filename_lower:
            sources_to_check = ["web", "bluray", "brrip", "bdrip", "hdtv", "dvd", "cam"]
            for src in sources_to_check:
                if src in media_filename_lower and src in sub_filename_lower:
                    source_matched = True
                    break

        if source_matched:
            score += 40

        # 2. RESOLUTION MATCH (+30 points)
        media_res = media_data.get("resolution")
        sub_res = sub_data.get("resolution")

        if not sub_res and media_res and str(media_res).lower() in sub_filename_lower:
            sub_res = media_res

        if media_res and sub_res and str(media_res).lower() == str(sub_res).lower():
            score += 30

        # 3. RELEASE GROUP MATCH (+30 points)
        # Perfect sync guarantee - same group = same encode = perfect timing
        media_group = media_data.get("release_group")
        sub_group = sub_data.get("release_group")

        if media_group and sub_group and str(media_group).lower() == str(sub_group).lower():
            score += 30

        return score