from automation import sync_students_from_google_sheet


def main():
    sync_result = sync_students_from_google_sheet()
    print(sync_result)


if __name__ == "__main__":
    main()
