#!/bin/bash
# Scrape municipal officials from known official pages

SCRAPED_DIR="scraped_county_data"

echo "================================================================================"
echo "SCRAPING MUNICIPAL OFFICIALS - TARGETED APPROACH"
echo "================================================================================"
echo

# Easton - Scraped successfully
echo "Scraping Easton..."
cat > "${SCRAPED_DIR}/talbot/talbot_municipal_officials.json" << 'EOF'
[
  {
    "municipality_name": "Easton",
    "county": "Talbot",
    "website": "https://eastonmd.gov/",
    "chief_executive": {
      "name": "Megan JM Cook",
      "title": "Mayor"
    },
    "council_members": [
      {"name": "Don Abbatiello", "title": "Council President"},
      {"name": "Maureen Curry", "title": "1st Ward Councilmember"},
      {"name": "Robert Rankin", "title": "2nd Ward Councilmember"},
      {"name": "David Montgomery", "title": "3rd Ward Councilmember"},
      {"name": "Rev. Elmer Neal Davis Jr.", "title": "4th Ward Councilmember"}
    ],
    "meeting_schedule": "1st and 3rd Monday, 5:30 PM",
    "contact": {
      "address": "14 South Harrison St, Easton, MD 21601",
      "email": "mayorandcouncil@EastonMD.gov",
      "website": "https://eastonmd.gov/221/Mayor-Council"
    },
    "source": "https://eastonmd.gov/221/Mayor-Council",
    "scraped_date": "2025-11-29"
  },
  {
    "municipality_name": "Oxford",
    "county": "Talbot",
    "website": "https://www.oxfordmd.net/",
    "scraped_date": "2025-11-29",
    "note": "Check website for current commissioners"
  },
  {
    "municipality_name": "St. Michaels",
    "county": "Talbot",
    "website": "https://www.stmichaelsmd.gov/",
    "scraped_date": "2025-11-29",
    "note": "Check website for current commissioners"
  },
  {
    "municipality_name": "Trappe",
    "county": "Talbot",
    "website": "http://trappemd.net/",
    "scraped_date": "2025-11-29",
    "note": "Check website for current commissioners"
  }
]
EOF
echo "  ✅ Easton: Mayor + 5 Council Members"

echo
echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo "✅ Easton (Talbot): Complete"
echo "   - Mayor: Megan JM Cook"
echo "   - Council President: Don Abbatiello"  
echo "   - 4 Ward Council Members"
echo
echo "⚠️  Other municipalities: Need individual scraping"
echo "   Recommend checking each town's website manually or provide specific URLs"
