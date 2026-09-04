import re


# ==========================================
# Helper: Strip HTML Tags
# ==========================================

def strip_html_tags(text):
    """Remove HTML tags from a string."""

    if not text:
        return ""

    clean = re.sub(r"<[^>]+>", "", text)

    return clean.strip()


# ==========================================
# Helper: Format Salary Range
# ==========================================

def format_salary_range(salary_min, salary_max):
    """Format salary range string."""

    if salary_min and salary_max:

        return (
            f"\u20b9{int(salary_min):,} - "
            f"\u20b9{int(salary_max):,}"
        )

    if salary_min:

        return f"From \u20b9{int(salary_min):,}"

    if salary_max:

        return f"Up to \u20b9{int(salary_max):,}"

    return "Not disclosed"


# ==========================================
# JobSuggestion DTO
# ==========================================

class JobSuggestion:
    """Data Transfer Object for external job search results."""

    def __init__(
        self,
        title,
        company,
        location,
        salary_min,
        salary_max,
        salary_range,
        description,
        redirect_url,
        created
    ):

        self.title = title
        self.company = company
        self.location = location
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.salary_range = salary_range
        self.description = description
        self.redirect_url = redirect_url
        self.created = created

    @staticmethod
    def from_adzuna(item):
        """Map an Adzuna API result item to a JobSuggestion."""

        title = strip_html_tags(
            item.get("title", "")
        )

        company = item.get(
            "company", {}
        ).get(
            "display_name", "Unknown Company"
        )

        location = item.get(
            "location", {}
        ).get(
            "display_name", "Unknown Location"
        )

        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")

        salary_range = format_salary_range(
            salary_min,
            salary_max
        )

        description = strip_html_tags(
            item.get("description", "")
        )

        redirect_url = item.get(
            "redirect_url", ""
        )

        created = item.get("created", "")

        return JobSuggestion(
            title=title,
            company=company,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_range=salary_range,
            description=description,
            redirect_url=redirect_url,
            created=created
        )

    def to_dict(self):
        """Convert JobSuggestion to dictionary."""

        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_range": self.salary_range,
            "description": self.description,
            "redirect_url": self.redirect_url,
            "created": self.created
        }
